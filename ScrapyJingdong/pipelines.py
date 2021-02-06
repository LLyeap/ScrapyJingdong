#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import time
import random
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.misc import arg_to_iter
from twisted.internet.defer import DeferredList
import json

import ScrapyJingdong.database as db
from ScrapyJingdong.items import SkuInfo

cursor = db.connection.cursor()


class ScrapyJingdongPipeline:
    """
    处理基本信息保存
    """

    def process_item(self, item, spider):
        if isinstance(item, SkuInfo):
            '''
            SkuInfo
            '''
            save_type = 'file'  # 选择存储sku基础信息的格式: file-文件/db-数据表

            if save_type == 'file':     # 以文件形式存储
                self.save_sku_info_file(item)
            else:
                exist = self.get_sku_info(item)     # 查找数据库里是否有该值

                if not exist:
                    try:
                        self.save_sku_info(item)    # 数据库存储
                    except Exception as e:
                        print(item)
                        print(e)
                else:
                    try:
                        self.update_sku_info(item)  # 数据库修改
                    except Exception as e:
                        print(item)
                        print(e)
        return item

    def get_sku_info(self, item):
        """
        DB 查看某个code的sku基本信息是否已存在
        :param item:
        :return:
        """
        sql = 'SELECT code FROM skus WHERE code = %s' % item['code']
        cursor.execute(sql)
        return cursor.fetchone()

    def save_sku_info(self, item):
        """
        DB 新增不存在的sku基本信息存储
        :param item:
        :return:
        """
        keys = item.keys()
        values = tuple(item.values())
        fields = ','.join(keys)
        temp = ','.join(['%s'] * len(keys))
        sql = 'INSERT INTO skus (%s) VALUES (%s)' % (fields, temp)
        cursor.execute(sql, tuple(i.strip() for i in values))
        return db.connection.commit()

    def update_sku_info(self, item):
        """
        DB 修改数据库已存储的值
        :param item:
        :return:
        """
        code = item.pop('code')
        keys = item.keys()
        values = list(item.values())
        values.append(code)
        fields = ['%s=' % i + '%s' for i in keys]
        sql = 'UPDATE skus SET %s WHERE code = %s' % (','.join(fields), '%s')
        cursor.execute(sql, values)
        return db.connection.commit()

    def save_sku_info_file(self, item):
        """
        sku基本信息存储到文本文件
        :param item:
        :return:
        """
        # 文件存储路径: ./storage/年月/日/sku_code/info.txt
        path = '%s/%s/%s/%s/info.json' % ('./storage',
                                         time.strftime("%Y%m", time.localtime()),
                                         time.strftime("%d", time.localtime()),
                                         item['code'])

        json = self.sku_info_to_json(item)  # 获取sku信息的文本格式
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json)

    def sku_info_to_json(self, item):
        """
        将sku的item转换为json字符串
        :param item:
        :return:
        """
        # 将item转换字典
        item_dict = dict(item)

        # 转换为json字符串并追加,逗号
        json_str = json.dumps(item_dict)

        return json_str


class ImagePipeline(ImagesPipeline):
    """
    处理图片下载
    """

    def process_item(self, item, spider):
        if isinstance(item, SkuInfo):
            '''
            SkuInfo 处理
            '''
            info = self.spiderinfo
            requests = arg_to_iter([])  # 存储图片下载请求
            if len(item['images']) > 0:     # 存在主图图片, 处理主图下载
                # 循环图片列表, 构建图片下载
                reqImages = arg_to_iter([self.get_media_requests(imgUrl, info) for imgUrl in item['images']])
                requests.extend(reqImages)
            if len(item['rich_text_urls']) > 0:     # 存在富文本内容图片, 处理富文本图片下载
                reqRichTextUrls = arg_to_iter([self.get_media_requests(richImgUrl, info) for richImgUrl in item['rich_text_urls']])
                requests.extend(reqRichTextUrls)
            # 处理图片下载
            dlist = [self._process_request(r, info, item) for r in requests]
            dfd = DeferredList(dlist, consumeErrors=True)
            return dfd.addCallback(self.item_completed, item, info)

    def get_media_requests(self, img_url, info):
        """
        下载图片时, 第一个执行的函数
        :param img_url:
        :param info:
        :return:
        """
        if img_url:
            return Request(img_url)

    def file_path(self, request, response=None, info=None):
        """
        下载图片时, 第二个执行的函数
        :param request:
        :param response:
        :param info:
        :return:
        """
        # 获取skuCode, 将图片资源以skuCode划分文件夹分组
        skuCode = info.spider.skuInfo['code']
        # 获取图片资源类型, 以及当前图片下载序号, 构建到文件名中, 方便排序
        reqUrl = request.url
        skuImageUrls = info.spider.skuInfo['images']
        skuRichTextUrls = info.spider.skuInfo['rich_text_urls']
        imageType = 'images'
        if reqUrl in skuImageUrls:
            index = skuImageUrls.index(reqUrl)
        else:
            index = skuRichTextUrls.index(reqUrl)
            imageType = 'rich_text_images'
        # 文件名格式为: 年月/日/sku_code/资源类型/2位序号 + 时分秒 + 随机
        return '%s/%s/%s/%s/%s.jpg' % (time.strftime("%Y%m", time.localtime()),
                                    time.strftime("%d", time.localtime()),
                                    skuCode,
                                    imageType,
                                    str(index).zfill(2) + time.strftime("%H%M%S", time.localtime()) + str(random.randint(10, 99)))

    def item_completed(self, results, item, info):
        """
        下载图片时, 第三个执行的函数
        :param results:
        :param item:
        :param info:
        :return:
        """
        paths = [x['path'] for ok, x in results if ok]
        # 将图片资源存储到相应字段
        # 根据__file_path__构建文件名方法, 可知split('/')第三个元素为类型
        imageUrls = [path for path in paths if path.split('/')[3] == 'images']
        imageUrls.sort()  # 由于__file_path__在处理文件名时做了序号前缀, 所以该出直接排序即可
        richTextUrls = [path for path in paths if path.split('/')[3] == 'rich_text_images']
        richTextUrls.sort()

        if paths:
            item['images'] = ''.join(imageUrls)
            item['rich_text_urls'] = ''.join(richTextUrls)
        else:
            item['images'] = ''
            item['rich_text_urls'] = ''
        return item

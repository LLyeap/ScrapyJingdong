#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import time
import random

import ScrapyJingdong.database as db

from ScrapyJingdong.items import SkuInfo

from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.python import to_bytes

from twisted.internet.defer import DeferredList

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
            exist = self.get_sku_info(item)

            if not exist:
                try:
                    self.save_sku_info(item)
                except Exception as e:
                    print(item)
                    print(e)
            else:
                try:
                    self.update_sku_info(item)
                except Exception as e:
                    print(item)
                    print(e)
        return item

    def get_sku_info(self, item):
        sql = 'SELECT code FROM skus WHERE code = %s' % item['code']
        cursor.execute(sql)
        return cursor.fetchone()

    def save_sku_info(self, item):
        keys = item.keys()
        values = tuple(item.values())
        fields = ','.join(keys)
        temp = ','.join(['%s'] * len(keys))
        sql = 'INSERT INTO skus (%s) VALUES (%s)' % (fields, temp)
        cursor.execute(sql, tuple(i.strip() for i in values))
        return db.connection.commit()

    def update_sku_info(self, item):
        code = item.pop('code')
        keys = item.keys()
        values = list(item.values())
        values.append(code)
        fields = ['%s=' % i + '%s' for i in keys]
        sql = 'UPDATE skus SET %s WHERE code = %s' % (','.join(fields), '%s')
        cursor.execute(sql, values)
        return db.connection.commit()


class ImagePipeline(ImagesPipeline):
    """
    处理图片下载
    """

    def process_item(self, item, spider):
        if isinstance(item, SkuInfo):
            '''
            SkuInfo 处理
            '''
            # TODO: 区分主图和富文本图
            info = self.spiderinfo
            requests = arg_to_iter([])
            if len(item['images']) > 0:
                reqImages = arg_to_iter([self.get_media_requests(imgUrl, info) for imgUrl in item['images']])
                requests.extend(reqImages)
            if len(item['rich_text_urls']) > 0:
                # 循环富文本图片列表, 构建图片下载
                reqRichTextUrls = arg_to_iter([self.get_media_requests(richImgUrl, info) for richImgUrl in item['rich_text_urls']])
                requests.extend(reqRichTextUrls)
            # 处理图片下载
            dlist = [self._process_request(r, info, item) for r in requests]
            dfd = DeferredList(dlist, consumeErrors=True)
            return dfd.addCallback(self.item_completed, item, info)

    def get_media_requests(self, richImgUrl, info):
        """
        下载图片时, 第一个执行的函数
        :param richImgUrl:
        :param info:
        :return:
        """
        if richImgUrl:
            return Request(richImgUrl)

    def file_path(self, request, response=None, info=None):
        """
        下载图片时, 第二个执行的函数
        :param request:
        :param response:
        :param info:
        :return:
        """
        # 获取skuCode, 将图片资源以文件夹分组
        skuCode = info.spider.skuInfo['code']
        # 获取图片资源类型, 并且当前图片下载号, 将下载文件按序号排序
        reqUrl = request.url
        skuImageUrls = info.spider.skuInfo['images']
        skuRichTextUrls = info.spider.skuInfo['rich_text_urls']
        imageType = 'images'
        if reqUrl in skuImageUrls:
            index = skuImageUrls.index(reqUrl)
        else:
            index = skuRichTextUrls.index(reqUrl)
            imageType = 'rich_text_images'
        # 年月/日/sku_code/资源类型/随机
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

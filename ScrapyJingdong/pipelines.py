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
            if len(item['rich_text_urls']) > 0:
                info = self.spiderinfo
                # 循环富文本图片列表, 构建图片下载
                requests = arg_to_iter([self.get_media_requests(richImgUrl, info) for richImgUrl in item['rich_text_urls']])
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
        return '%s/%s/%s.jpg' % (time.strftime("%Y%m", time.localtime()),
                                 time.strftime("%d", time.localtime()),
                                 time.strftime("%H%M%S", time.localtime()) + str(random.randint(10, 99)))

    def item_completed(self, results, item, info):
        """
        下载图片时, 第三个执行的函数
        :param results:
        :param item:
        :param info:
        :return:
        """
        print(results)
        # TODO: 需要进行排序
        image_paths = [x['path'] for ok, x in results if ok]
        if image_paths:
            item['rich_text_urls'] = ''.join(image_paths)
        else:
            item['rich_text_urls'] = ''
        return item

import json
import requests
import js2xml
from js2xml.utils.vars import get_vars
from scrapy import Request, Spider
import re

from ScrapyJingdong.items import SkuInfo


class SkuInfoSpider(Spider):    # 需要继承scrapy.Spider类

    name = "sku_info"   # 定义蜘蛛名

    # 定义变量
    skuInfo = SkuInfo()

    def start_requests(self):   # 由此方法通过下面链接爬取页面
        # 定义爬取的链接
        urls = [
            'https://item.jd.com/30278478342.html',
        ]
        for url in urls:
            yield Request(url=url, callback=self.parse)  # 爬取到的页面如何处理？提交给parse方法处理

    def parse(self, response):
        """
        接收 start_requests 回调
        :param response:
        :return:
        """

        if 404 == response.status:
            print(response.url)
        else:
            self.skuInfo['code'] = self.get_sku_id(response)
            self.skuInfo['image'] = 'http://img30.360buyimg.com/popWareDetail/jfs/t1/147977/4/7331/135469/5f506ed1E784062f1/1b774961ec58590f.jpg'
            self.skuInfo['name'] = self.get_sku_name(response)    # 获取商品名称
            self.skuInfo['jd_price'] = self.get_sku_jd_price(response)    # 获取京东金额

            richTextUrl = self.get_page_config_desc_url(response)   # 获取富文本内容url
            yield Request(url=richTextUrl, callback=self.parseRichText)

    def parseRichText(self, response):
        """
        进一层回调处理富文本内容
        :param response:
        :return:
        """

        # 正式处理富文本内容
        content = str(json.loads(response.text)['content'])
        regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"   # 正则匹配图片url
        data = re.findall(regex, content)   # 正则提取图片url列表
        self.skuInfo['rich_text_urls'] = data

        return self.skuInfo

    def get_sku_id(self, response):
        """
        获取商品code
        :param response:
        :return:
        """
        jd_url = response.url   # 获取当前页面的url, 从url中获取京东商品id
        skuId = jd_url.split('/')[-1].strip(".html")
        return skuId

    def get_page_config(self, response):
        """
        获取页面head/script/pageConfig内容
        :param response:
        :return:
        """

        regx = 'normalize-space(//head/script[@charset="gbk"]/text())'
        data = response.xpath(regx).extract_first()
        jsData = get_vars(js2xml.parse(data))   # jsData取出来是个字典
        return jsData

    def get_page_config_desc_url(self, response):
        jsData = self.get_page_config(response)
        descUrl = 'https:' + jsData['pageConfig']['product']['desc']
        return descUrl

    def get_page_config_main_sku_id(self, response):
        jsData = self.get_page_config(response)
        mainSkuId = jsData['pageConfig']['product']['mainSkuId']
        return mainSkuId

    def get_sku_name(self, response):
        """
        获取商品名称
        :param response:
        :return:
        """
        regx = 'normalize-space(//div[@class="sku-name"]/text())'
        data = response.xpath(regx).extract_first()

        name = data if data else '名称获取错误'
        return name

    def get_sku_jd_price(self, response):
        """
        获取京东金额
        :param response:
        :return:
        """
        skuCode = self.get_sku_id(response)
        price_url = "https://p.3.cn/prices/mgets?skuIds=J_" + skuCode   # price信息是通过jsonp获取，可以通过开发者工具中的script找到它的请求地址
        response_price = requests.get(price_url)    # 请求京东金额
        jdPrice = json.loads(response_price.text)[0]['p']

        jdPrice = jdPrice if jdPrice else 0.00
        return jdPrice

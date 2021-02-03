# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class SkuInfo(Item):
    id = Field()
    code = Field()
    name = Field()
    jd_price = Field()
    image = Field()
    rich_text_urls = Field()

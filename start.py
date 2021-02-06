from scrapy import cmdline

cmdline.execute("scrapy crawl sku_info -d sku_code=30278478342".split())
# cmdline.execute("scrapy crawl sku_rich_text".split())

# import os
#
# os.system("scrapy crawl sku_info")
# os.system("scrapy crawl sku_rich_text")


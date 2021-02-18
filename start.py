from scrapy import cmdline

cmdline.execute("scrapy crawl sku_info -a sku_code=30278478342".split())

# import os
#
# os.system("scrapy crawl sku_info -a sku_code=30278478342")


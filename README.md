# 直接运行

直接使用命令 `scrapy crawl sku_info` 启动爬虫

或者调用根目录下的 start.py 文件 `python start.py`

# 借用scrapyd部署

参考文档: https://www.cnblogs.com/gambler/p/12059541.html

**注意: ** 他的文档里有错别字, 注意关注 scrapy 和 scrapyd, 文档有几处错误的将scrapyd误写为scrapy了

```python
# 1. 按照环境
pip install scrapyd
pip install scrapy-client

# 2. 启动scrapyd服务
scrapyd

# 3. 配置scrapy项目, `scrapy.cfg` 文件

# 4. 上传scrapy项目
python scrapyd-deploy –l
# python scrapyd-deploy [target] -p [project]
python scrapyd-deploy JD -p JD_sku

# 5. 调用api
curl http://localhost:6800/schedule.json -d project=JD_sku -d spider=sku_info


# 6. 安装scrapydweb
pip install scrapydweb

# 7. 运行scrapydweb
scrapydweb

```
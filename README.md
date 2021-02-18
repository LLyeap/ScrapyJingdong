# 直接运行

直接使用命令 `scrapy crawl sku_info -a sku_code=<京东商品的编码>` 启动爬虫

或者调用根目录下的 start.py 文件 `python start.py`

# 借用scrapyd部署

参考文档: https://www.cnblogs.com/gambler/p/12059541.html

**注意: ** 他的文档里有错别字, 注意关注 scrapy 和 scrapyd, 文档有几处错误的将scrapyd误写为scrapy了

```python
# 更多依赖包在requirements.txt里
# pip install -r requirements.txt

# 1. 按照环境
pip install scrapyd
pip install scrapy-client

# 2. 启动scrapyd服务
scrapyd
# 远程服务器部署涉及到修改scrapyd的配置文件中bind_address, 使其可以外部访问
# find / -name scrapyd   # 你也可以在scrapyd跑起来的服务中找到这个路径
# cd /root/anaconda3/envs/crawl3/lib/python3.8/site-packages/scrapyd
# vim default_scrapyd.conf
# 修改 bind_address = 0.0.0.0

# 3. 配置scrapy项目, `scrapy.cfg` 文件

# 4. 上传scrapy项目
python scrapyd-deploy –l
# python scrapyd-deploy [target] -p [project]
python scrapyd-deploy JD -p JD_sku
# 如果在deploy时出现报错 `Deploy failed: <urlopen error [Errno 110] Connection timed out>`, 请查看服务器防火墙. ps: 阿里云服务器的安全组

# 5. 调用api
curl http://localhost:6800/schedule.json -d project=JD_sku -d spider=sku_info -d sku_code=30278478342


# 6. 安装scrapydweb
pip install scrapydweb

# 7. 运行scrapydweb
scrapydweb

```
data = '''
[settings]
default = baiduCrawler.settings
[deploy]
#url = http://localhost:6800/
project = baiduCrawler
'''

with open('scrapy.cfg', 'w') as f:
    f.write(data)
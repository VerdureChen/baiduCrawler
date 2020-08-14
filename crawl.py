from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess


def crawl(Q, spider_list, keyword, pages, hostname, dbname, username, password):
    # CrawlerProcess
    s = get_project_settings()
    s['MYSQL_USERNAME'] = username
    s['MYSQL_PASSWORD'] = password
    s['HOSTNAME'] = hostname
    s['DBNAME'] = dbname
    process = CrawlerProcess(s)
    #Q.clear()
    for spi in spider_list:
        process.crawl(spi, Q=Q, keywords=keyword, pages=pages)
    process.start()

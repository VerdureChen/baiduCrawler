# -*- coding: utf-8 -*-
import scrapy
import urllib.parse
import requests
import re
import datetime
from ..items import baijiahaoItem
import pymongo
import hashlib
import os
import sqlite3
import pickle
import pymysql

import logging


class BaijiahaoSpider(scrapy.Spider):
    name = 'baijiahao'
    allowed_domains = ['baidu.com']
    # start_urls = ['http://baidu.com/']
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    }
    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': header,
        'DOWNLOAD_DELAY': 0.5,
        'DOWNLOADER_MIDDLEWARES': {
            # 'baiduCrawler.middlewares.BaiducrawlerDownloaderMiddleware': 543,
        },
        'MONGO_URI': '127.0.0.1',
        'MONGO_DB': 'baijiahaoSpider',
        'ITEM_PIPELINES': {
            'baiduCrawler.pipelines.SQL3Pipeline': 300,
        },
        # 'BREAKING_POINT': True
    }

    # 连接数据库，对比数据
    mongo_uri = custom_settings['MONGO_URI']
    mongo_db = custom_settings['MONGO_DB']
    client = pymongo.MongoClient(host=mongo_uri, port=27017)
    db = client[mongo_db]

    # con = sqlite3.connect("news.sqlite")
    # cu = con.cursor()

    # username = custom_settings['MYSQL_USERNAME']
    # password = custom_settings['MYSQL_PASSWORD']
    # try:
    #     con = pymysql.connect("localhost", username, password, "NEWSDB", autocommit=1)
    #     cu = con.cursor()
    #     con.commit()
    # except:
    #     con = pymysql.connect("localhost", username, password, autocommit=1)
    #     cu = con.cursor()
    #     cu.execute('CREATE DATABASE NEWSDB')
    #     con.commit()

    # page = 2
    # keys = ['电网', '停电']
    base_url = 'https://www.baidu.com/s?medium=2&tn=news&word={}&pn={}'

    # 更新的新闻数量
    new_news = 0

    def __init__(self, Q=None, keywords=None, pages=1,  *args, **kwargs):
        super(BaijiahaoSpider, self).__init__(*args, **kwargs)
        self.keys=keywords.split(' ')
        self.page = int(pages)
        self.Q = Q

    def baijiahao_log(self):
        '''
        logger函数，在文件和控制台输出信息
        :return:
        '''
        # 创建logger，如果参数为空则返回root logger
        logger = logging.getLogger("baijiahaoLogger")
        logger.setLevel(logging.DEBUG)  # 设置logger日志等级​
        # 这里进行判断，如果logger.handlers列表为空，则添加，否则，直接去写日志
        if not logger.handlers:
            # 创建handler
            fh = logging.FileHandler("baijiahaolog.log", encoding="utf-8")
            ch = logging.StreamHandler()
            # 设置输出日志格式
            formatter = logging.Formatter(
                fmt="%(asctime)s %(name)s %(filename)s %(message)s",
                datefmt="%Y/%m/%d %X"
            )
            # 为handler指定输出格式
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            # 为logger添加的日志处理器
            logger.addHandler(fh)
            logger.addHandler(ch)
        return logger  # 直接返回logger

    def start_requests(self):
        logger = self.baijiahao_log()
        logger.info(
            '---------------------------------baijiahao Spider started {}----------------------------------------'.format(
                datetime.date.today().strftime('%Y-%m-%d')
            )
        )
        # start_urls= []
        for key in self.keys:
            # self.fangwenDict[key] = []
            for i in range(self.page):
                num = i * 10
                # start_url = self.search_url.format(urllib.parse.quote(i), 0, 20, 0)
                # self.header['referer']='https://www.zhihu.com/search?q={}&type=content&range=3m'.format(urllib.parse.quote(i))
                # self.header['referer'] = 'https://www.zhihu.com'
                url = self.base_url.format(urllib.parse.quote(key), num)
                # print(url)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    dont_filter=True,
                    meta={"keyword": key, 're_time': 1},
                )
                # print('start finish')
            #     break
            # break

    def parse(self, response):
        '''
        对爬取到的百度页面进行解析，获得百家号的链接
        如果未爬取到百度的检索结果，则重新请求百度链接
        :param response:
        :return:
        '''
        logger = self.baijiahao_log()
        key = response.meta.get('keyword')
        re_time = response.meta.get('re_time')
        logger.info("【{}】【start url】:{}".format(key, response.url))
        hrefs = response.xpath(".//div[@id='content_left']/div/div[@class='result']/h3/a/@href").extract()
        if len(hrefs) < 5 and re_time == 1:
            yield scrapy.Request(response.url, dont_filter=True,
                                 callback=self.parse, meta={"keyword": key, 're_time': 2}, )
        # colItem = baijiahaoItem()
        # b_collection = self.db[colItem.collection]
        # sql = 'SELECT COUNT(*) FROM {} WHERE url=\"{}\" AND keyword=\"{}\";'
        for hre in hrefs:
            logger.info("【{}】【sub url】:{}, 【start url】:{}".format(key, hre, response.url))
            # hre = self.convert_url(hre)
            pattern = 'https://baijiahao.baidu.com/'

            # try:
            #     self.cu.execute(sql.format(colItem.collection, hre, key))
            #     self.con.commit()
            #     c = self.cu.fetchone()[0]
            # except:
            #     sql2 = "CREATE TABLE IF NOT EXISTS baijiahao(keyword TEXT,url TEXT,article_title TEXT, author_name TEXT," \
            #           "publish_time TEXT, account_authentication TEXT, article_text TEXT, spi_date TEXT)"
            #     self.cu.execute(sql2)
            #     self.con.commit()
            #     self.cu.execute(sql.format(colItem.collection, hre, key))
            #     self.con.commit()
            #     c = self.cu.fetchone()[0]

            # logger.info("去重"+str(c)+'  '+sql.format(colItem.collection, hre, key))
            if re.match(pattern, hre) != None:
                yield scrapy.Request(hre, dont_filter=True,
                                     meta={"keyword": key},
                                     callback=self.parse_baijiahao)  ##不同关键词可能有同一问题
                # break

        # print('parse finish')

    def parse_baijiahao(self, response):
        logger = self.baijiahao_log()
        html_str = response

        b_item = baijiahaoItem()
        keyword = response.meta.get('keyword')

        b_item['url'] = response.url
        b_item['keyword'] = keyword
        b_item['article_title'] = html_str.xpath('.//div[@class="article-title"]/h2/text()').extract_first()
        b_item['author_name'] = html_str.xpath('.//p[@class="author-name"]/text()').extract_first()
        dt = html_str.xpath('.//span[@class="date"]/text()').extract_first()
        try:
            if re.search('([0-9]+-[0-9]+-[0-9]+)', dt):
                dt = '20' + re.search('([0-9]+-[0-9]+-[0-9]+)', dt).group(1)
            elif re.search('([0-9]+-[0-9]+)', dt):
                dt = str(datetime.datetime.now().year) + '-' + re.search('([0-9]+-[0-9]+)', dt).group(1)
            else:
                dt = 'NULL'
        except:
            dt = 'NULL'
        b_item['publish_time'] = dt
        b_item['spi_date'] = datetime.date.today().isoformat()
        b_item['account_authentication'] = html_str.xpath(
            './/span[@class="account-authentication"]/text()').extract_first()
        b_item['article_text'] = ''.join(html_str.xpath('.//span[@class="bjh-p"]/text()').extract()).strip()
        # logger.info('【keyword】: {}, 【add news】：{}'.format(keyword, b_item['article_title']))
        # self.new_news = self.new_news + 1
        # logger.info('【keyword】:{}, 【total new news】:{}'.format(keyword, self.new_news))
        # self.Q.put('【百度资讯】【关键词】:{}, 【新收集新闻数量】:{}'.format(keyword, self.new_news))
        yield b_item

    # def close(spider, reason):
    #     spider.Q.put('百度百家号爬取结束')
    #     #spider.Q.join()
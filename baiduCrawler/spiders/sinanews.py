# -*- coding: utf-8 -*-
import scrapy
import urllib.parse
import requests
import re
import datetime
from ..items import sinanewsItem
import pymongo
import hashlib
import os
import pickle

import logging

class SinanewsSpider(scrapy.Spider):
    name = 'sinanews'
    allowed_domains = ['sina.com.cn']
    #start_urls = ['http://sina.com.cn/']

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
        'MONGO_DB': 'sina_newsSpider',
        'ITEM_PIPELINES': {
            'baiduCrawler.pipelines.BaiducrawlerPipeline': 300,
        },
        # 'BREAKING_POINT': True
    }

    # 连接数据库，对比数据
    mongo_uri = custom_settings['MONGO_URI']
    mongo_db = custom_settings['MONGO_DB']
    client = pymongo.MongoClient(host=mongo_uri, port=27017)
    db = client[mongo_db]

    # page = 2
    # keys = ['电网', '停电']
    base_url = 'https://search.sina.com.cn/?q={}&c=news&from=channel&col=&range=all&source=&country=&size=10&stime=&etime=&time=&dpc=0&a=&ps=0&pf=0&page={}'

    # 更新的新闻数量
    new_news = 0

    #已访问url
    visited_url = {}

    def __init__(self, keywords=None, pages=1,  *args, **kwargs):
        super(SinanewsSpider, self).__init__(*args, **kwargs)
        self.keys=keywords.split(',')
        self.page = int(pages)


    def sinanews_log(self):
        '''
        logger函数，在文件和控制台输出信息
        :return:
        '''
        # 创建logger，如果参数为空则返回root logger
        logger = logging.getLogger("sinanewsLogger")
        logger.setLevel(logging.DEBUG)  # 设置logger日志等级​
        # 这里进行判断，如果logger.handlers列表为空，则添加，否则，直接去写日志
        if not logger.handlers:
            # 创建handler
            fh = logging.FileHandler("sinanewslog.log", encoding="utf-8")
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
        logger = self.sinanews_log()
        logger.info(
            '---------------------------------sinanews Spider started {}----------------------------------------'.format(
                datetime.date.today().strftime('%Y-%m-%d')
            )
        )
        # start_urls= []
        for key in self.keys:
            # self.fangwenDict[key] = []
            self.visited_url[key] = []
            for i in range(self.page):
                num = i+1
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
        logger = self.sinanews_log()
        key = response.meta.get('keyword')
        re_time = response.meta.get('re_time')
        logger.info("【{}】【start url】:{}".format(key, response.url))
        hrefs = response.xpath(".//h2/a/@href").extract()
        scti = response.xpath(".//h2/span[@class='fgray_time']/text()").extract()
        if len(hrefs) < 5 and re_time == 1:
            yield scrapy.Request(response.url, dont_filter=True,
                                 callback=self.parse, meta={"keyword": key, 're_time': 2}, )
        colItem = sinanewsItem()
        b_collection = self.db[colItem.collection]
        for hre, st in zip(hrefs, scti):
            st = st.strip().split(' ')
            sc = st[0]
            tm = st[1]
            logger.info("【{}】【sub url】:{}, 【start url】:{}".format(key, hre, response.url))
            # hre = self.convert_url(hre)
            #pattern = 'https://baijiahao.baidu.com/'
            if b_collection.count_documents({'url': hre, 'keyword': key}) != 0:
                logger.info("【{}去重】【sub url】:{}, 【start url】:{}".format(key, hre, response.url))
            if b_collection.count_documents({'url': hre, 'keyword': key}) == 0:  ##可能发现重复时前个页面还未解析完，用字典再过滤一遍
                if hre not in self.visited_url[key]:
                    self.visited_url[key].append(hre)
                    print(hre, sc, tm)
                    yield scrapy.Request(hre, dont_filter=True,
                                         meta={"keyword": key, "sc": sc, "tm": tm},
                                         callback=self.parse_sinanews)  ##不同关键词可能有同一问题

                    # break

        # print('parse finish')

    def parse_sinanews(self, response):
        logger = self.sinanews_log()
        html_str = response

        b_item = sinanewsItem()
        keyword = response.meta.get('keyword')

        b_item['url'] = response.url
        b_item['keyword'] = keyword
        b_item['article_title'] = html_str.xpath('.//h1/text()').extract_first()
        #b_item['author_name'] = html_str.xpath('.//p[@class="author-name"]/text()').extract_first()
        dt = html_str.xpath('.//span[@class="date"]/text()').extract_first()
        b_item['publish_time'] = response.meta.get('tm')
        b_item['article_source'] = response.meta.get('sc')
        try:
            b_item['article_text'] = ''.join([i.strip() for i in html_str.xpath('.//div[@class="article"]/descendant::p//text()').extract()])
            if b_item['article_text'] == '':
                return
        except:
            return
        b_collection = self.db[b_item.collection]
        if b_collection.count_documents({'article_title': b_item['article_title'], 'keyword': keyword}) != 0:
            logger.info('【title去重】【keyword】: {}, 【news】：{}'.format(keyword, b_item['article_title']))
            return
        logger.info('【keyword】: {}, 【add news】：{}'.format(keyword, b_item['article_title']))
        self.new_news = self.new_news + 1
        logger.info('【keyword】:{}, 【total new news】:{}'.format(keyword, self.new_news))
        yield b_item

# -*- coding: utf-8 -*-
import scrapy
import urllib.parse
import requests
import re
import datetime
from ..items import BaiducrawlerItem
from ..items import zhihuQuestionItem
import pymongo
import hashlib
import os
import pickle

import logging
from lxml import etree

class TmpSpider(scrapy.Spider):
    '''
    根据关键词列表在百度进行搜索，对结果中的知乎问答进行爬取
    由于知乎加密限制，使用selenium对页面渲染后进行爬取
    '''
    name = 'tmp'
    allowed_domains = ['www.baidu.com', 'www.zhihu.com']
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
           'baiduCrawler.middlewares.BaiducrawlerDownloaderMiddleware': 543,
        },
        'MONGO_URI': '127.0.0.1',
        'MONGO_DB': 'zhihuSpider',
        'ITEM_PIPELINES': {
           'baiduCrawler.pipelines.BaiducrawlerPipeline': 300,
        },
        'BREAKING_POINT': True
    }

    #连接数据库，对比数据
    mongo_uri = custom_settings['MONGO_URI']
    mongo_db = custom_settings['MONGO_DB']
    client = pymongo.MongoClient(host=mongo_uri, port=27017)
    db = client[mongo_db]


    # #设置爬取的百结果度页数
    # page = 2
    # #设置查询关键词列表
    # keys = ["电网", "停电"]

    base_url = 'https://www.baidu.com/s?wd={}&pn={}'
    zhihu_url= 'https://www.zhihu.com/question/{}/answers/updated?page={}'
    # start_urls = []
    # for i in range(page):
    #     num = i * 10
    #     start_urls.append(base_url.format(urllib.parse.quote(key+" "+"知乎"), num))

    #对每次爬虫运行时的新收集到的问题、回答
    #以及更新的问题、回答数量进行统计
    new_question_count=0
    update_question_count = 0

    new_answer_count = 0
    update_answer_count = 0

    #对每个关键词在本次运行中已访问的问题id进行记录，防止重复访问
    fangwenDict={}

    from_breakingPoint = custom_settings['BREAKING_POINT']

    current_path = os.path.dirname(os.path.abspath(__file__))
    vlog_path = os.path.join(os.path.dirname(current_path), 'visit_log')
    if not os.path.exists(vlog_path):
        os.mkdir(vlog_path)


    finish_file_path = os.path.join(vlog_path, 'vlog_{}.pkl'.format(datetime.date.today().strftime('%Y_%m_%d')))
    if os.path.isfile(finish_file_path):
        f = open(finish_file_path, 'rb')
        finish_dic = pickle.load(f)
        f.close()
    else:
        finish_dic = {}

    def __init__(self, keywords=None, pages=1,  *args, **kwargs):
        super(TmpSpider, self).__init__(*args, **kwargs)
        self.keys=keywords.split(',')
        self.page = int(pages)

    def start_requests(self):
        logger = self.zhi_log()
        logger.info('---------------------------------zhihu Spider started {}----------------------------------------'.format(
            datetime.date.today().strftime('%Y-%m-%d')
        )
        )
        #start_urls= []
        for key in self.keys:
            self.fangwenDict[key]=[]
            for i in range(self.page):
                num = i * 10
                #start_url = self.search_url.format(urllib.parse.quote(i), 0, 20, 0)
                #self.header['referer']='https://www.zhihu.com/search?q={}&type=content&range=3m'.format(urllib.parse.quote(i))
                #self.header['referer'] = 'https://www.zhihu.com'
                url = self.base_url.format(urllib.parse.quote(key+" "+"知乎"), num)
                #print(url)
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    dont_filter=True,
                    meta={"keyword": key},
                )
                # print('start finish')
            #     break
            # break



    # 将百度的url转成真实的url
    def convert_url(self, url):
        resp = requests.get(url=url,
                            headers=self.header,
                            allow_redirects=False
                            )
        return resp.headers['Location']



    def parse(self, response):
        '''
        对爬取到的百度页面进行解析，获得知乎问题的链接
        如果未爬取到百度的检索结果，则重新请求百度链接
        :param response:
        :return:
        '''
        logger = self.zhi_log()
        key = response.meta.get('keyword')
        logger.info("【{}】【start url】:{}".format(key, response.url))
        hrefs = response.xpath(".//div[@id='content_left']/div/h3/a/@href").extract()
        if len(hrefs)< 5:
            yield scrapy.Request(response.url, dont_filter=True,
                                 callback=self.parse, meta={"keyword": key},)
        for hre in hrefs:
            logger.info("【{}】【sub url】:{}, 【start url】:{}".format(key, self.convert_url(hre), response.url))
            hre = self.convert_url(hre)
            pattern = 'https://www.zhihu.com/question/(\d+)'
            if re.match(pattern, hre) != None:
                question_num = re.match(pattern, hre).group(1)
                #print(question_num)
                if question_num in self.fangwenDict[key]:
                    logger.info("keyword: {}, 去重id: {}".format(key, question_num))
                    continue
                else:
                    self.fangwenDict[key].append(question_num)

                if self.from_breakingPoint:
                    if key in self.finish_dic and question_num in self.finish_dic[key]:
                        if self.finish_dic[key][question_num] == 9999:
                            continue
                        page = self.finish_dic[key][question_num]+1
                        logger.info("断点，问题{}从第{}页开始请求".format(question_num, page))
                    else:
                        page = 1
                else:
                    page = 1
                #question_num = '22064032'

                yield scrapy.Request(self.zhihu_url.format(question_num, page), dont_filter=True,
                                     meta={"page": page, "question_num": question_num, "keyword": key},
                                     callback=self.parse_zhihu)   ##不同关键词可能有同一问题
                #break
        #print('parse finish')


    def parse_zhihu(self, response):
        '''
        对知乎问答页面进行解析，答案按照时间顺序排序，如果存在下一页，则继续请求下一页
        :param response:
        :return:
            zhiItem: 记录问题的相关信息，包括搜索关键词、问题id、问题url、问题正文、问题关注者数量、问题浏览量、回答总数
            item: 记录每个回答的信息，包括
        '''
        logger = self.zhi_log()
        html_str = response

        #提取问题的相关信息
        keyword = response.meta.get('keyword')
        question_num = response.meta.get('question_num')
        question_url = response.url  #此处为了便于计算究竟抓取到哪一页，没有对page信息进行更改
        question_text = html_str.xpath('.//h1/text()').extract_first()
        # print(question_text)
        # return None
        question_guanzhu = html_str.xpath('.//strong[@class="NumberBoard-itemValue"]/@title').extract()[0]
        question_read = html_str.xpath('.//strong[@class="NumberBoard-itemValue"]/@title').extract()[1]
        answer_num = html_str.xpath('.//h4/span/text()[1]').extract_first()
        #print("total answer number:", answer_num)

        zhiItem = zhihuQuestionItem()
        zhiItem['keyword'] = keyword
        zhiItem['question_num'] = question_num
        zhiItem['question_url'] = question_url
        zhiItem['question_text'] = question_text
        zhiItem['question_guanzhu'] = question_guanzhu
        zhiItem['question_read'] = question_read
        zhiItem['count_answer'] = re.search('([0-9,]+)', answer_num).group(1)
        #计算问题各项属性的hash值，判断是否需要更新数据
        try:
            hash_text = zhiItem['keyword'] + zhiItem['question_num'] + zhiItem['question_text'] + zhiItem['question_guanzhu'] + zhiItem['question_read'] + zhiItem['count_answer']
        except:
            hash_text = ''
            for k, v in dict(zhiItem):
                if v is None:
                    logger.error('【valueError】：{}:{} in {}'.format(k, v, zhiItem['question_num']))
                else:
                    hash_text = hash_text+zhiItem[k]

        md5 = hashlib.md5()
        md5.update(hash_text.encode('utf-8'))
        zhiItem['question_hash'] = md5.hexdigest()

        #获取当前爬取知乎页面的页码
        page = response.meta.get('page')

        #问题的集合
        q_collection = self.db[zhiItem.collection]

        #如果该关键词下这个问题id没有出现过，则作为新问题添加
        #如果存在，则对比hash值，如果不相等，更新该条数据
        if q_collection.count_documents({'question_num': question_num, 'keyword': keyword}) == 0:
            logger.info("【new question】:{}, 【keyword】:{}, 【total answer number】:{}".format(
                zhiItem['question_text'], zhiItem['keyword'], zhiItem['count_answer']
            )
            )
            self.new_question_count = self.new_question_count+1
            assert page == 1
            yield zhiItem
        else:
            q_hashs =q_collection.find({'question_num': question_num, 'keyword': keyword})
            assert q_hashs.count() == 1
            for q in q_hashs:
                q_hash = q['question_hash']
                if q_hash != zhiItem['question_hash']:
                    logger.info("【update question】:" + zhiItem['question_text']+' 【keyword】:'+zhiItem['keyword'])
                    q_collection.update({'question_num': question_num, 'keyword': keyword}, zhiItem)
                    self.update_question_count = self.update_question_count+1
                else:
                    pass


        #对答案进行解析
        #html = etree.HTML(html_str)
        #answers = html_str.xpath('.//span[@class="RichText ztext CopyrightRichText-richText"]')
        answers = html_str.xpath('.//div[@class="ContentItem AnswerItem"]')
        #print(len(answers))
        for answer in answers:
            item = BaiducrawlerItem()
            item['keyword']= keyword
            item['question_num'] = question_num
            item['question_url'] = question_url
            item['question_text'] = question_text
            item['answer_name'] = answer.xpath('./div[1]/div/meta[@itemprop="name"]/@content').extract_first()
            item['answer_url'] = answer.xpath('./meta[@itemprop="url"]/@content').extract_first()
            time = ' '.join(answer.xpath('./div[2]/div[2]/div/a/span/text()').extract()).strip()

            #时间有多种格式：如果是今年的回答，则为month-day形式；
            #如果是昨天的回答，则显示具体时间，如10：57
            #如果是24小时内的回答，则显示__前，统一划为今天
            #如果不是今年的回答，则是year-month-day形式
            #这里统一为year-month-day形式
            if re.search('([0-9]+-[0-9]+-[0-9]+)', time):
                time = re.search('([0-9]+-[0-9]+-[0-9]+)', time).group(1)
            elif re.search('([0-9]+-[0-9]+)', time):
                d = re.search('([0-9]+-[0-9]+)', time).group(1)
                time = str(datetime.datetime.now().year)+'-'+ d
            elif re.search('前', time):
                time = datetime.date.today().strftime('%Y-%m-%d')
            elif re.search('昨天', time):
                time = (datetime.date.today() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')
            else:
                time = 'ukn'
                logger.info("【timeError】:"+item['answer_url'])

            item['answer_time'] = time

            #对答案正文进行解析，如果是多段则多一个p标签
            if answer.xpath('./div[2]/div[1]/span[@class="RichText ztext CopyrightRichText-richText"]/text()').extract() == []:
                item['answer_text'] = ''.join(answer.xpath('./div[2]/div[1]/span[@class="RichText ztext CopyrightRichText-richText"]/p/text()').extract()).strip()
            else:
                item['answer_text'] = ''.join(answer.xpath('./div[2]/div[1]/span[@class="RichText ztext CopyrightRichText-richText"]/text()').extract()).strip()
            #print(item['answer_text'])

            #对点赞情况进行提取
            zan = answer.xpath('./div[2]/div[3]/span/button[1]/@aria-label').extract_first()
            try:
                if "万" in zan:
                    z = re.search('([0-9/.]+)', zan).group(1)
                    z =int(z) * 10000
                    item['dianzan_num'] = str(z)
                else:
                    item['dianzan_num'] = re.search('([0-9]+)', zan).group(1)
            except:
                try:
                    zan = answer.xpath('./div[2]/div[3]/div/span/button[1]/@aria-label').extract_first()
                    item['dianzan_num'] = re.search('([0-9]+)', zan).group(1)
                except:
                    logger.info("【refineAnswer】:"+item['answer_url'])
                    item['dianzan_num'] = 'ukn'

            #对评论数量进行提取
            comment = answer.xpath('./div[2]/div[3]/button[1]/text()').extract_first()
            if comment=="添加评论":
                item['comment_num'] = '0'
            else:
                try:
                    cnum=re.search('([0-9]+)', comment).group(1)
                    item['comment_num'] = cnum
                except:
                    try:
                        comment = answer.xpath('./div[2]/div[3]/div/button[1]/text()').extract_first()
                        cnum = re.search('([0-9]+)', comment).group(1)
                        item['comment_num'] = cnum
                    except:
                        logger.info("【commentError】"+item['answer_url'])
                        item['comment_num'] = 'ukn'

            #计算回答信息的hash值
            hsh_txt = item['keyword']+item['question_num']+item['question_text']+item['answer_name']+item['answer_time']+item['dianzan_num']+item['comment_num']
            md5_2 = hashlib.md5()
            md5_2.update(hsh_txt.encode('utf-8'))
            item['answer_hash'] = md5_2.hexdigest()

            #回答的集合
            a_collection = self.db[item.collection]
            if a_collection.count_documents({'answer_url': item['answer_url'], 'keyword': keyword}) == 0:
                self.new_answer_count = self.new_answer_count + 1
                yield item
            else:
                a_hashs = a_collection.find({'answer_url': item['answer_url'], 'keyword': keyword})
                assert a_hashs.count() == 1
                for a in a_hashs:
                    a_hash = a['answer_hash']
                    if a_hash != item['answer_hash']:
                        a_collection.update({'answer_url': item['answer_url'], 'keyword': keyword}, item)
                        self.update_answer_count = self.update_answer_count + 1
                    else:
                        pass


        #每解析完一页，记录新增和更新信息
        logger.info(
            '【question number】:{}, 【page】:{}, 【total_newQ】:{}, 【total_upQ】:{}, 【total_newA】:{}, 【total_upA】:{}'.format(
                zhiItem['question_num'], page, self.new_question_count,
                self.update_question_count, self.new_answer_count, self.update_answer_count
            )
        )

        if self.from_breakingPoint:
            f = open(self.finish_file_path, 'wb')
            if keyword in self.finish_dic:
                self.finish_dic[keyword][question_num] = page
            else:
                self.finish_dic[keyword] = {}
                self.finish_dic[keyword][question_num] = page
            if len(html_str.xpath('.//button[@class="Button PaginationButton PaginationButton-next Button--plain"]').extract())==0:
                self.finish_dic[keyword][question_num] = 9999
            pickle.dump(self.finish_dic, f)
            f.close()


        page = page+1
        if html_str.xpath('.//button[@class="Button PaginationButton PaginationButton-next Button--plain"]'):
            yield scrapy.Request(self.zhihu_url.format(question_num, page), dont_filter=True,
                                     meta={"page": page, "question_num": question_num, "keyword": keyword},
                                     callback=self.parse_zhihu)



    def zhi_log(self):
        '''
        logger函数，在文件和控制台输出信息
        :return:
        '''
        # 创建logger，如果参数为空则返回root logger
        logger = logging.getLogger("zhihuLogger")
        logger.setLevel(logging.DEBUG)  # 设置logger日志等级​
        # 这里进行判断，如果logger.handlers列表为空，则添加，否则，直接去写日志
        if not logger.handlers:
            # 创建handler
            fh = logging.FileHandler("zhi.log", encoding="utf-8")
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
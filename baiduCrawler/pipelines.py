# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import sqlite3
import logging
import pymysql
import datetime
import time
import random

class BaiducrawlerPipeline(object):
    '''
    连接mongodb数据库
    '''
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_uri=crawler.settings.get('MONGO_URI'), mongo_db=crawler.settings.get('MONGO_DB'))

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(host=self.mongo_uri, port=27017)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        self.db[item.collection].insert(dict(item))

        return item

    def close_spider(self, spider):
        self.client.close()


class SQL3Pipeline(object):
    def __init__(self, username, password, Q, dbname, hostname):
        self.username = username
        self.password = password
        self.dbname = dbname
        self.hostname = hostname
        self.new_question_count = 0
        self.update_question_count = 0
        self.new_answer_count = 0
        self.update_answer_count = 0
        self.new_bai_news = 0
        self.new_sina_news = 0
        self.Q = Q

        self.zhi_logger = self.log_log('zhihu_log.log', 'zhihulog')
        self.bai_logger = self.log_log('bai_log.log', 'baidulog')
        self.sina_logger = self.log_log('sina_log.log', 'sinalog')

        self.bai_logger.info(
            '---------------------------------baijiahao Spider started {}----------------------------------------'.format(
                datetime.date.today().strftime('%Y-%m-%d')
            )
        )

        self.sina_logger.info(
            '---------------------------------sinanews Spider started {}----------------------------------------'.format(
                datetime.date.today().strftime('%Y-%m-%d')
            )
        )

        self.zhi_logger.info(
            '---------------------------------zhihu Spider started {}----------------------------------------'.format(
                datetime.date.today().strftime('%Y-%m-%d')
            )
        )

    @classmethod
    def from_crawler(cls, crawler):
        return cls(username=crawler.settings.get('MYSQL_USERNAME'), password=crawler.settings.get('MYSQL_PASSWORD'),
                   Q=crawler.spider.Q, dbname=crawler.settings.get('DBNAME'), hostname=crawler.settings.get('HOSTNAME'))

    def open_spider(self,spider):
        # self.con = sqlite3.connect("news.sqlite")
        # self.cu = self.con.cursor()
        try:
            self.con = pymysql.connect(self.hostname, self.username, self.password, self.dbname, charset='utf8', autocommit=1)
            self.cu = self.con.cursor()
        except:
            self.con = pymysql.connect(self.hostname, self.username, self.password, charset='utf8', autocommit=1)
            self.cu = self.con.cursor()
            self.cu.execute('CREATE DATABASE {}'.format(self.dbname))

    def baijiahao_insert(self, item):
        sql = 'SELECT COUNT(*) FROM {} WHERE url=\"{}\" AND keyword=\"{}\";'
        self.cu.execute(sql.format(item.collection, item['url'], item['keyword']))
        self.con.commit()
        c = self.cu.fetchone()[0]
        if c != 0:
            if item['article_title'] is None:
                item['article_title'] = 'NULL'
            self.bai_logger.info('【百家号去重】:' + item['article_title'] + str(c))
        else:
            insert_sql = "insert into {0}({1}) values ({2})".format(item.collection,
                                                                    ','.join(item.fields.keys()),
                                                                    ','.join(['%s'] * len(item.fields.keys())))
            #self.cu.execute(insert_sql, tuple([item[k] if item[k] is not None else 'NULL'for k in item.fields.keys()]))
            self.cu.execute(insert_sql, tuple([item[k] for k in item.fields.keys()]))
            self.con.commit()
            self.new_bai_news = self.new_bai_news + 1
            self.bai_logger.info('【keyword】: {}, 【add news】：{}'.format(item['keyword'], item['article_title']))
        self.bai_logger.info('【keyword】:{}, 【total new news】:{}'.format(item['keyword'], self.new_bai_news))
        time.sleep(random.random())
        self.Q.put('【百度资讯】【关键词】:{}, 【新收集新闻数量】:{}'.format(item['keyword'], self.new_bai_news))


    def sinanews_insert(self, item):
        sql = 'SELECT COUNT(*) FROM {} WHERE article_title=\"{}\" AND keyword=\"{}\"'
        self.cu.execute(sql.format(item.collection, item['article_title'], item['keyword']))
        print("【查询】"+sql.format(item.collection, item['article_title'], item['keyword']))
        self.con.commit()
        c = self.cu.fetchone()[0]
        if c != 0:
            if item['article_title'] is None:
                item['article_title'] = 'NULL'
            self.sina_logger.info('【新浪新闻去重】:' + item['article_title'] + str(c))
        else:
            insert_sql = "insert into {0}({1}) values ({2})".format(item.collection,
                                                                    ','.join(item.fields.keys()),
                                                                    ','.join(['%s'] * len(item.fields.keys())))
            #self.cu.execute(insert_sql, tuple([item[k] if item[k] is not None else 'NULL'for k in item.fields.keys()]))
            self.cu.execute(insert_sql, tuple([item[k] for k in item.fields.keys()]))
            print('【insert sql】: ', insert_sql, ' ', tuple([item[k] if item[k] is not None else 'NULL'for k in item.fields.keys()]))
            self.con.commit()
            self.new_sina_news = self.new_sina_news + 1
            self.sina_logger.info('【keyword】: {}, 【add news】：{}'.format(item['keyword'], item['article_title']))

        self.sina_logger.info('【keyword】:{}, 【total new news】:{}'.format(item['keyword'], self.new_sina_news))
        time.sleep(random.random())
        self.Q.put('【新浪新闻】【关键词】:{}, 【新收集新闻数量】:{}'.format(item['keyword'], self.new_sina_news))


    def zhihuQuestion_insert(self, item):
        sql = 'SELECT COUNT(*) FROM {} WHERE question_num=\"{}\" AND keyword=\"{}\"'
        self.cu.execute(sql.format(item.collection, item['question_num'], item['keyword']))
        self.con.commit()
        c = self.cu.fetchone()[0]
        if c == 0:
            # logger.info("【new question】:{}, 【keyword】:{}, 【total answer number】:{}".format(
            #     zhiItem['question_text'], zhiItem['keyword'], zhiItem['count_answer']
            # )
            # )
            self.new_question_count = self.new_question_count+1
            insert_sql = "insert into {0}({1}) values ({2})".format(item.collection,
                                                                    ','.join(item.fields.keys()),
                                                                    ','.join(['%s'] * len(item.fields.keys())))
            self.con.commit()
            #self.cu.execute(insert_sql, tuple([item[k] if item[k] is not None else 'NULL'for k in item.fields.keys()]))
            self.cu.execute(insert_sql, tuple([item[k] for k in item.fields.keys()]))
        else:
            sql3 = "SELECT question_hash FROM {} WHERE question_num=\"{}\" AND keyword=\"{}\""
            self.cu.execute(sql3.format(item.collection, item['question_num'], item['keyword']))

            q_hash = self.cu.fetchone()[0]
            if q_hash != item['question_hash']:
                # logger.info("【update question】:" + zhiItem['question_text']+' 【keyword】:'+zhiItem['keyword'])
                sql4 = 'UPDATE {} SET question_text=\"{}\", question_guanzhu=\"{}\", question_read=\"{}\", ' \
                       'count_answer=\"{}\", question_hash=\"{}\", spi_date=\"{}\" ' \
                       'WHERE question_num=\"{}\" AND keyword=\"{}\"'.format(item.collection, item['question_text'],
                                                                             item['question_guanzhu'], item['question_read'],
                                                                             item['count_answer'],
                                                                             item['question_hash'], item['spi_date'],
                                                                             item['question_num'], item['keyword'])
                self.cu.execute(sql4)
                self.con.commit()
                self.update_question_count = self.update_question_count+1
            else:
                pass
        self.zhi_logger.info(
            '【question number】:{}, 【total_newQ】:{}, 【total_upQ】:{}, 【total_newA】:{}, 【total_upA】:{}'.format(
                item['question_num'], self.new_question_count,
                self.update_question_count, self.new_answer_count, self.update_answer_count
            )
        )
        time.sleep(random.random())
        self.Q.put('【知乎问答】【收集新问题】:{}, 【更新问题】:{}, 【收集新回答】:{}, 【更新回答】:{}'.format(
            self.new_question_count,
            self.update_question_count, self.new_answer_count, self.update_answer_count))

    def zhihu_insert(self, item):
        sql = 'SELECT COUNT(*) FROM {} WHERE answer_url=\"{}\" AND keyword=\"{}\"'
        self.cu.execute(sql.format(item.collection, item['answer_url'], item['keyword']))
        self.con.commit()
        c = self.cu.fetchone()[0]
        if c == 0:
            self.new_answer_count = self.new_answer_count + 1
            insert_sql = "insert into {0}({1}) values ({2})".format(item.collection,
                                                                    ','.join(item.fields.keys()),
                                                                    ','.join(['%s'] * len(item.fields.keys())))
            #self.cu.execute(insert_sql, tuple([item[k] if item[k] is not None else 'null'for k in item.fields.keys()]))
            self.cu.execute(insert_sql, tuple([item[k] for k in item.fields.keys()]))
            self.con.commit()

        else:
            sql3 = "SELECT answer_hash FROM {} WHERE answer_url=\"{}\" AND keyword=\"{}\""
            self.cu.execute(sql3.format(item.collection, item['answer_url'], item['keyword']))
            self.con.commit()
            a_hash = self.cu.fetchone()[0]

            if a_hash != item['answer_hash']:
                sql4 = 'UPDATE {} SET question_text=\"{}\", question_num=\"{}\", answer_name=\"{}\", ' \
                       'answer_time=\"{}\", answer_hash=\"{}\", dianzan_num=\"{}\", spi_date=\"{}\" , comment_num=\"{}\"' \
                       'WHERE answer_url=\"{}\" AND keyword=\"{}\"'.format(item.collection,
                                                                             item['question_text'],
                                                                             item['question_num'],
                                                                             item['answer_name'],
                                                                             item['answer_time'],
                                                                             item['answer_hash'],
                                                                             item['dianzan_num'],
                                                                             item['spi_date'],
                                                                             item['comment_num'],
                                                                             item['answer_url'],
                                                                             item['keyword'])
                self.cu.execute(sql4)
                self.con.commit()
                # a_collection.update({'answer_url': item['answer_url'], 'keyword': keyword}, item)
                self.update_answer_count = self.update_answer_count + 1
            else:
                pass

        self.zhi_logger.info(
            '【question number】:{}, 【total_newQ】:{}, 【total_upQ】:{}, 【total_newA】:{}, 【total_upA】:{}'.format(
                item['question_num'], self.new_question_count,
                self.update_question_count, self.new_answer_count, self.update_answer_count
            )
        )
        time.sleep(random.random())
        self.Q.put('【知乎问答】【收集新问题】:{}, 【更新问题】:{}, 【收集新回答】:{}, 【更新回答】:{}'.format(
            self.new_question_count,
            self.update_question_count, self.new_answer_count, self.update_answer_count))

    def process_item(self, item, spider):
        #print(','.join(item.fields.keys()),','.join([item[k] for k in item.fields.keys()]))

        try:
            if item.collection == 'baijiahao':
                self.baijiahao_insert(item)


            elif item.collection == 'sinanews':
                self.sinanews_insert(item)


            elif item.collection == 'zhihu':
                self.zhihu_insert(item)


            elif item.collection == 'zhihuQuestion':
                self.zhihuQuestion_insert(item)


        except:
            if item.collection == 'sinanews':
                sql = "CREATE TABLE IF NOT EXISTS sinanews(keyword TEXT,url TEXT,article_title TEXT, article_source TEXT," \
                      "publish_time TEXT, article_text TEXT, spi_date TEXT)"
                self.cu.execute(sql)
                self.con.commit()
                self.sinanews_insert(item)

            elif item.collection == 'baijiahao':
                sql = "CREATE TABLE IF NOT EXISTS baijiahao(keyword TEXT,url TEXT,article_title TEXT, author_name TEXT," \
                      "publish_time TEXT, account_authentication TEXT, article_text TEXT, spi_date TEXT)"
                self.cu.execute(sql)
                self.con.commit()
                self.baijiahao_insert(item)

            elif item.collection == 'zhihu':
                sql = "CREATE TABLE IF NOT EXISTS zhihu(keyword TEXT,question_url TEXT,question_text TEXT, question_num INTEGER ," \
                      "answer_name TEXT, answer_url TEXT, answer_time TEXT, answer_text TEXT, dianzan_num INTEGER , comment_num INTEGER ," \
                      "answer_hash TEXT, spi_date TEXT)"
                self.cu.execute(sql)
                self.con.commit()
                self.zhihu_insert(item)

            elif item.collection == 'zhihuQuestion':
                sql = "CREATE TABLE IF NOT EXISTS zhihuQuestion(keyword TEXT,question_url TEXT,question_text TEXT, question_num INTEGER ," \
                      "question_guanzhu INTEGER , question_read INTEGER , count_answer INTEGER , question_hash TEXT, spi_date TEXT)"
                self.cu.execute(sql)
                self.con.commit()
                self.zhihuQuestion_insert(item)

            else:
                print('【collection error】')
            # insert_sql = "insert into {0}({1}) values ({2})".format(item.collection,
            #                                                         ','.join(item.fields.keys()),
            #                                                         ','.join(['?'] * len(item.fields.keys())))
            # self.cu.execute(insert_sql, tuple([item[k] if item[k]!=None else 'NULL'for k in item.fields.keys()]))


        return item

    def log_log(self, f_path, logger_name):
        '''
        logger函数，在文件和控制台输出信息
        :return:
        '''
        # 创建logger，如果参数为空则返回root logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)  # 设置logger日志等级​
        # 这里进行判断，如果logger.handlers列表为空，则添加，否则，直接去写日志
        if not logger.handlers:
            # 创建handler
            fh = logging.FileHandler(f_path, encoding="utf-8")
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

    def close_spider(self,spider):
        #print('finish:', spider.name)
        time.sleep(random.random())
        if spider.name == 'tmp':
            spider.Q.put('知乎问答爬取结束')
        elif spider.name == 'baijiahao':
            spider.Q.put('百度百家号爬取结束')
        elif spider.name == 'sinanews':
            spider.Q.put('新浪新闻爬取结束')
        self.con.close()
        #spider.Q.join()
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class BaiducrawlerItem(scrapy.Item):
    '''
    答案item
    '''
    # define the fields for your item here like:
    # name = scrapy.Field()
    collection = 'zhihu'
    keyword = Field()
    question_url = Field()
    question_text = Field()
    question_num = Field()
    answer_name = Field()
    answer_url = Field()
    answer_time = Field()
    answer_text = Field()
    dianzan_num = Field()
    comment_num = Field()
    answer_hash = Field()
    spi_date = Field()
    # count_answer = Field()

class zhihuQuestionItem(scrapy.Item):
    '''
    问题item
    '''
    collection = 'zhihuQuestion'
    keyword = Field()
    question_url = Field()
    question_text = Field()
    question_num = Field()
    question_guanzhu = Field()
    question_read = Field()
    count_answer = Field()
    question_hash = Field()
    spi_date = Field()

class baijiahaoItem(scrapy.Item):
    '''
    百家号item
    '''
    collection = 'baijiahao'
    keyword = Field()
    url = Field()
    article_title = Field()
    author_name = Field()
    publish_time = Field()
    account_authentication = Field()
    article_text = Field()
    spi_date = Field()


class sinanewsItem(scrapy.Item):
    '''
    sina news
    '''
    collection = 'sinanews'
    keyword = Field()
    url = Field()
    article_title = Field()
    article_source = Field()
    publish_time = Field()
    #account_authentication = Field()
    article_text = Field()
    spi_date = Field()
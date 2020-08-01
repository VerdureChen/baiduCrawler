import os
from scrapy.commands import ScrapyCommand
from scrapy.utils.conf import arglist_to_dict
from scrapy.utils.python import without_none_values
from scrapy.exceptions import UsageError
import configparser
import scrapy.commands.crawl as crawl

class Command(crawl.Command):
    requires_project = True

    def syntax(self):
        '''
        此处通过运行本程序运行所有爬虫，因此不必提供spider的名字
        :return:
        '''
        return "[options]"

    def short_desc(self):
        return "Run all spider"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option("-a", dest="spargs", action="append", default=[], metavar="NAME=VALUE",
                          help="set spider argument (may be repeated)")
        parser.add_option("-o", "--output", metavar="FILE",
                          help="dump scraped items into FILE (use - for stdout)")
        parser.add_option("-t", "--output-format", metavar="FORMAT",
                          help="format to use for dumping items with -o")
        #添加配置文件的名称，其中dest的值Conf可以在run函数中使用opts.Conf调用
        parser.add_option("-c", "--config-file", dest="Conf",
                          help="config file path")

    def run(self, args, opts):
        #获取comd.py的当前目录
        current_path = os.path.dirname(os.path.abspath(__file__))
        configpath = opts.Conf
        #合成config文件的地址
        conf_path = os.path.join(os.path.dirname(current_path), configpath)
        cf = configparser.ConfigParser()
        cf.read(conf_path, encoding="utf-8")
        #获得项目下所有爬虫列表
        spider_list = self.crawler_process.spiders.list()
        for spid in spider_list:
            keywords = cf.get(spid, 'keywords')
            pages = cf.get(spid, 'pages')
            #对每个爬虫传入其需要的参数
            self.crawler_process.crawl(spid, keywords=keywords, pages=pages, **opts.spargs)
        # keywords = cf.get('baijiahao', 'keywords')
        # pages = cf.get('baijiahao', 'pages')
        # self.crawler_process.crawl('baijiahao', keywords=keywords, pages=pages, **opts.spargs)
        self.crawler_process.start()
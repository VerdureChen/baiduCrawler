from multiprocessing import freeze_support
freeze_support()
import sys
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel, QSqlQuery
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableView, QWidget, QLabel, QVBoxLayout, QHBoxLayout, \
    QHeaderView, QLineEdit, QPushButton, QCheckBox, QGridLayout, QComboBox, QTabWidget, QSpinBox, QSplitter, QDialog,\
    QDialogButtonBox, QSplashScreen, QTextEdit, QTextBrowser, QWidget, QMainWindow, QFormLayout
from PyQt5.QtCore import QThread, pyqtSignal, QFile, QTextStream
from baiduCrawler.spiders.tmp import TmpSpider
from baiduCrawler.spiders.baijiahao import  BaijiahaoSpider
from baiduCrawler.spiders.sinanews import SinanewsSpider
from multiprocessing import Process, Manager, JoinableQueue, Pipe
import ctypes
import scrapy
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
import logging
import os
import configparser
import pymysql
import crawl
import scrapy.spiderloader
import scrapy.statscollectors
import scrapy.logformatter
import scrapy.dupefilters
import scrapy.squeues
import jieba
import scrapy.extensions.spiderstate
import scrapy.extensions.corestats
import scrapy.extensions.telnet
import scrapy.extensions.logstats
import scrapy.extensions.memusage
import scrapy.extensions.memdebug
import scrapy.extensions.feedexport
import scrapy.extensions.closespider
import scrapy.extensions.debug
import scrapy.extensions.httpcache
import scrapy.extensions.statsmailer
import scrapy.extensions.throttle
import scrapy.downloadermiddlewares.chunked
import scrapy.core.scheduler
import scrapy.core.engine
import scrapy.core.scraper
import scrapy.core.spidermw
import scrapy.core.downloader
import selenium
import scrapy.downloadermiddlewares.stats
import scrapy.downloadermiddlewares.httpcache
import scrapy.downloadermiddlewares.cookies
import scrapy.downloadermiddlewares.useragent
import scrapy.downloadermiddlewares.httpproxy
import scrapy.downloadermiddlewares.ajaxcrawl
import scrapy.downloadermiddlewares.chunked
import scrapy.downloadermiddlewares.decompression
import scrapy.downloadermiddlewares.defaultheaders
import scrapy.downloadermiddlewares.downloadtimeout
import scrapy.downloadermiddlewares.httpauth
import scrapy.downloadermiddlewares.httpcompression
import scrapy.downloadermiddlewares.redirect
import scrapy.downloadermiddlewares.retry
import scrapy.downloadermiddlewares.robotstxt
import jieba.posseg as pseg
from gensim import corpora, models
import scrapy.spidermiddlewares.depth
import scrapy.spidermiddlewares.httperror
import scrapy.spidermiddlewares.offsite
import scrapy.spidermiddlewares.referer
import scrapy.spidermiddlewares.urllength
from textProcess.process import textPro
import scrapy.pipelines

import scrapy.core.downloader.handlers.http
import scrapy.core.downloader.contextfactory
from scrapy import signals
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from scrapy.http import HtmlResponse
import time
import zipfile

class LogThread(QThread):

    def __init__(self, gui):
        super(LogThread, self).__init__()
        self.gui = gui
        self.count = 0
        self.gui_logger = self.log_log('gui.log', 'gui_logger')

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

    def run(self):
        print("thread running!")
        while True:
            if not self.gui.Q.empty():
                s = str(self.gui.Q.get())
                print(s)
                self.gui_logger.info(s)
                self.gui.Q.task_done()
                if '爬取结束' in s:
                    if '新浪' in s:
                        self.gui.label_sina_finish.setText("完成！")
                    if '知乎' in s:
                        self.gui.label_zhi_finish.setText("完成！")
                    if '百度' in s:
                        self.gui.label_baidu_finish.setText("完成！")
                    print(s, self.count, len(self.gui.spider_list))
                    self.count = self.count+1
                    if self.count == len(self.gui.spider_list):
                        # self.gui.db_connect()
                        # self.sql_exec()
                        self.count = 0
                        self.gui.spider_list = []
                        self.gui.st.setText('开始')
                        #QMessageBox.information(self.gui, '提示', '爬取完成！')
                        break
                else:
                    if '新浪' in s:
                        self.gui.label6.setText(s)
                    elif '百度' in s:
                        self.gui.label5.setText(s)
                    elif '知乎' in s:
                        self.gui.label1.setText(s)

                # 睡眠10毫秒，否则太快会导致闪退或者显示乱码
            self.msleep(10)


# def crawl(Q, spider_list, keyword, pages, hostname, dbname, username, password):
#     # CrawlerProcess
#     s = get_project_settings()
#     s['MYSQL_USERNAME'] = username
#     s['MYSQL_PASSWORD'] = password
#     s['HOSTNAME'] = hostname
#     s['DBNAME'] = dbname
#     process = CrawlerProcess(s)
#     #Q.clear()
#     for spi in spider_list:
#         process.crawl(spi, Q=Q, keywords=keyword, pages=pages)
#     process.start()


class Dialog(QDialog):
    dialogSignel = pyqtSignal(int, str, str, str, str)
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        #self.login = QWidget(self)

        self.setWindowIcon(QIcon(res_path('icon2.ico')))
        self.grid_layout = QGridLayout()
        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        self.count = 0
        self.setWindowTitle('连接数据库')
        self.hostname_label = QLabel('Host name:', self)
        self.database_label = QLabel('Database name:', self)
        self.user_label = QLabel('Username:', self)
        self.pwd_label = QLabel('Password:', self)
        self.hostname_line = QLineEdit(self)
        self.dbname_line = QLineEdit(self)
        self.user_line = QLineEdit(self)
        self.pwd_line = QLineEdit(self)
        self.pwd_line.setEchoMode(QLineEdit.Password)
        self.checkbox1 = QCheckBox('保存设置', self)
        self.login_button = QPushButton('连接', self)
        self.close_button = QPushButton('取消', self)

        current_path = os.path.dirname(os.path.abspath(__file__))
        self.ini_file_path = os.path.join(current_path, 'info.ini')
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.ini_file_path):
            self.config.read(self.ini_file_path, encoding="utf-8")
            rm = self.config.get("user_info", "remember")
            if rm == "1":
                self.host_name = self.config.get("user_info", "host_name")
                self.db_name = self.config.get("user_info", "db_name")
                self.user_name = self.config.get("user_info", "user_name")
                self.password = self.config.get("user_info", "password")
                self.checkbox1.setChecked(True)
                self.hostname_line.setText(self.host_name)
                self.dbname_line.setText(self.db_name)
                self.user_line.setText(self.user_name)
                self.pwd_line.setText(self.password)
        else:
            f = open(self.ini_file_path, 'w')
            f.close()
            self.config.read(self.ini_file_path, encoding="utf-8")


        self.layout_init()
        self.button_init()

    def layout_init(self):
        self.grid_layout.addWidget(self.hostname_label, 0, 0, 1, 1)
        self.grid_layout.addWidget(self.hostname_line, 0, 1, 1, 1)
        self.grid_layout.addWidget(self.database_label, 1, 0, 1, 1)
        self.grid_layout.addWidget(self.dbname_line, 1, 1, 1, 1)
        self.grid_layout.addWidget(self.user_label, 2, 0, 1, 1)
        self.grid_layout.addWidget(self.user_line, 2, 1, 1, 1)
        self.grid_layout.addWidget(self.pwd_label, 3, 0, 1, 1)
        self.grid_layout.addWidget(self.pwd_line, 3, 1, 1, 1)
        self.h_layout.addWidget(self.login_button)
        self.h_layout.addWidget(self.close_button)
        self.v_layout.addLayout(self.grid_layout)
        self.v_layout.addWidget(self.checkbox1)
        self.v_layout.addLayout(self.h_layout)

        self.setLayout(self.v_layout)

    def button_init(self):
        self.close_button.clicked.connect(self.close)
        self.login_button.clicked.connect(self.check)

    def check(self):
        hostname = self.hostname_line.text()
        dbname = self.dbname_line.text()
        username = self.user_line.text()
        pwd = self.pwd_line.text()
        if not hostname or not dbname or not username or not pwd:
            QMessageBox.information(self, '提示', '请完整填写信息!')
        else:
            self.count = self.count+1
            self.dialogSignel.emit(self.count, hostname, dbname, username, pwd)
            print('sending')

    def closeEvent(self, QCloseEvent):
        if not self.config.has_section("user_info"):
            self.config.add_section("user_info")
        if self.checkbox1.checkState() == 2:
            self.config.set("user_info", "remember", "1")
            self.config.set("user_info", "host_name", self.hostname_line.text())
            self.config.set("user_info", "db_name", self.dbname_line.text())
            self.config.set("user_info", "user_name", self.user_line.text())
            self.config.set("user_info", "password", self.pwd_line.text())
        else:
            self.config.set("user_info", "remember", "0")
            self.config.set("user_info", "host_name", '')
            self.config.set("user_info", "db_name", '')
            self.config.set("user_info", "user_name", '')
            self.config.set("user_info", "password", '')

        self.config.write(open(self.ini_file_path, "w"))

class showFullText(QDialog):
    saveSignal = pyqtSignal(int, int, int, str)
    def __init__(self, parent=None):
        super(showFullText, self).__init__(parent)
        self.processer = textPro()


    def layout_init2(self):
        self.h_layout2 = QHBoxLayout()
        self.v_layout2 = QVBoxLayout()
        self.save_button = QPushButton('保存', self)
        self.close_button = QPushButton('取消', self)
        self.h_layout2.addWidget(self.save_button)
        self.h_layout2.addWidget(self.close_button)
        self.v_layout2.addWidget(self.title_label)
        self.v_layout2.addWidget(self.text_edit)
        self.v_layout2.addLayout(self.h_layout2)
        self.setLayout(self.v_layout2)

    def layout_init1(self):
        # self.setWhatsThis('this is')
        self.text_browser = QTextBrowser(self)
        self.h_layout0 = QHBoxLayout()
        self.h_layout1 = QHBoxLayout()
        self.v_layout1 = QVBoxLayout()
        self.h_layout3 = QHBoxLayout()
        self.grid_layout = QGridLayout()
        self.POS_button = QPushButton('词性标注', self)
        self.wordsplit_button = QPushButton('分词', self)
        self.save_button = QPushButton('保存', self)
        self.close_button = QPushButton('取消', self)
        self.h_layout1.addWidget(self.save_button)
        self.h_layout1.addWidget(self.wordsplit_button)
        self.h_layout1.addWidget(self.POS_button)
        self.h_layout1.addWidget(self.close_button)
        self.h_layout0.addWidget(self.title_label)
        right_widget = QWidget()  # 创建一个右侧部件
        self.right_widget_layout = QGridLayout()  # 创建一个网格布局
        right_widget.setLayout(self.right_widget_layout)  # 设置右侧部件的布局为网格布局
        self.h_layout0.addWidget(right_widget)
        self.h_layout3.addWidget(self.text_edit)
        self.h_layout3.addWidget(self.text_browser)
        self.v_layout1.addLayout(self.h_layout0)
        self.v_layout1.addLayout(self.h_layout3)
        self.v_layout1.addLayout(self.h_layout1)
        self.setLayout(self.v_layout1)





    def showText(self, current_page_index, current_col, current_row, current_data):
        self.data = current_data
        self.current_page_index = current_page_index
        self.current_col = current_col
        self.current_row = current_row
        self.text_edit = QTextEdit(self)
        self.text_edit.textChanged.connect(self.set_text_func)
        self.text_edit.setText(current_data)
        self.setWindowTitle('显示全文')
        self.title_label = QLabel('正文:', self)
        if current_page_index == 0:
            col_title = ['关键词', '问题url', '问题', '问题ID', '回答者', '回答url', '回答时间', '回答正文', '点赞数', '评论数', '', '爬取时间']
            col_change = [2, 7]
            self.title_label.setText(col_title[current_col]+'：')
            if current_col in col_change:
                self.layout_init1()
            else:
                self.layout_init2()
        elif current_page_index == 1:
            col_title = ['关键词', '问题url', '问题', '问题ID', '问题关注量', '问题浏览量', '回答数量', '', '爬取时间']
            col_change = [2]
            self.title_label.setText(col_title[current_col]+'：')
            if current_col in col_change:
                self.layout_init1()
            else:
                self.layout_init2()
        elif current_page_index == 2:
            col_title = ['关键词', '文章url', '文章标题', '作者姓名', '发表时间', '来源', '正文', '爬取时间']
            col_change = [2, 6]
            self.title_label.setText(col_title[current_col]+'：')
            if current_col in col_change:
                self.layout_init1()
            else:
                self.layout_init2()
        elif current_page_index == 3:
            col_title = ['关键词', '问题url', '文章标题', '来源', '发表时间', '正文', '爬取时间']
            col_change = [2, 5]
            self.title_label.setText(col_title[current_col]+'：')
            if current_col in col_change:
                self.layout_init1()
            else:
                self.layout_init2()

        self.button_init()

    def set_text_func(self):
        self.data = self.text_edit.toPlainText()

    def button_init(self):
        self.close_button.clicked.connect(self.close)
        self.save_button.clicked.connect(self.save_data)
        try:
            self.wordsplit_button.clicked.connect(self.wdsplit)
            self.POS_button.clicked.connect(self.POS)
        except:
            pass

    def save_data(self):
        self.saveSignal.emit(self.current_page_index, self.current_col, self.current_row, self.data)

    def wdsplit(self):
        while self.right_widget_layout.count():
            child = self.right_widget_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        result = self.processer.word_split(self.data)
        result = "\n\n ".join(result)
        self.text_browser.setText(result)

    def POS(self):
        # 遍历右侧布局中的子部件，将其删除
        while self.right_widget_layout.count():
            child = self.right_widget_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.btn = QPushButton('词性标注对照表', self)
        # self.btn.setFixedSize(150, 100)
        self.right_widget_layout.addWidget(self.btn)  # 将文本部件添加到右侧布局中。
        self.btn.clicked.connect(self.showPic)
        result = self.processer.POS(self.data)
        result = "\n\n".join(result)
        self.text_browser.setText(result)

    def showPic(self):
        self.pic_widget = QDialog(self)
        lab1 = QLabel(self)
        lab1.setPixmap(QPixmap("./POS.png"))
        vbox = QVBoxLayout()
        vbox.addWidget(lab1)
        self.pic_widget.setLayout(vbox)
        self.pic_widget.setWindowTitle("词性标注对照表")
        self.pic_widget.show()

class DemoWidget(QWidget):
    fullTextSignal = pyqtSignal(int, int, int, str)
    def __init__(self):
        super(DemoWidget, self).__init__()


        #self.db_connect()

        #self.crawl_thread = CrawlThread(self)
        self.TB = QTabWidget(self)
        # self.table_init()
        self.setWindowIcon(QIcon(res_path('icon2.ico')))

        #self.table3 = QTableView(self)
        #self.TB.currentChanged.connect(lambda: print(self.TB.currentIndex()))
        self.label1 = QLabel("知乎收集器", self)
        self.label5 = QLabel("百度百家号收集器", self)
        self.label6 = QLabel("新浪新闻收集器", self)
        self.label2 = QLabel("关键词（用空格分隔）：",self)
        self.label3 = QLabel("选择数据源：", self)
        self.label4 = QLabel("页码：", self)
        self.label_sina_finish = QLabel("就绪", self)
        self.label_zhi_finish = QLabel("就绪", self)
        self.label_baidu_finish = QLabel("就绪", self)
        self.spinbox = QSpinBox(self)
        self.spinbox.setRange(1, 10)  # 1
        self.spinbox.setSingleStep(1)  # 2
        self.spinbox.setValue(1)
        self.inpt = QLineEdit(self)
        self.checkbox1 = QCheckBox('知乎问答', self)
        self.checkbox2 = QCheckBox('百度百家号', self)
        self.checkbox3 = QCheckBox('新浪新闻', self)
        self.st = QPushButton("开始", self)
        self.ad = QPushButton("添加", self)
        self.dl = QPushButton("删除", self)
        self.rn = QPushButton("刷新", self)
        self.sets = QPushButton("设置", self)
        self.set_buttton_disabled()
        #self.sql_exec()

        self.splitter1 = QSplitter(Qt.Vertical)
        self.log_thread = LogThread(self)
        # self.Q = Manager().Queue()
        self.Q = JoinableQueue()
        self.spider_list = []

        self.h_layout = QHBoxLayout()
        self.h_layout2 = QHBoxLayout()
        self.h_layout3 = QHBoxLayout()
        self.h_layout4 = QHBoxLayout()
        self.h_start_finish = QGridLayout()
        self.h_ad_dl = QHBoxLayout()
        self.v_layout = QVBoxLayout()
        self.v_layout2 = QVBoxLayout()

        #self.checkbox_init()
        self.button_init()
        #self.database_init()


    def database_init(self):
        try:
            self.con = pymysql.connect(self.hostname, self.username, self.pwd, self.dbname, charset='utf8', autocommit=1)
            self.cu = self.con.cursor()
        except:
            self.con = pymysql.connect(self.hostname, self.username, self.pwd, charset='utf8', autocommit=1)
            self.cu = self.con.cursor()
            self.cu.execute('CREATE DATABASE {}'.format(self.dbname))
            self.con.commit()
            self.cu.execute('USE {}'.format(self.dbname))
            self.con.commit()
            sql = "CREATE TABLE IF NOT EXISTS sinanews(keyword TEXT,url TEXT,article_title TEXT, article_source TEXT," \
                  "publish_time TEXT, article_text TEXT, spi_date TEXT)"
            self.cu.execute(sql)
            self.con.commit()
            sql2 = "CREATE TABLE IF NOT EXISTS baijiahao(keyword TEXT,url TEXT,article_title TEXT, author_name TEXT," \
                  "publish_time TEXT, account_authentication TEXT, article_text TEXT, spi_date TEXT)"
            self.cu.execute(sql2)
            self.con.commit()
            sql3 = "CREATE TABLE IF NOT EXISTS zhihu(keyword TEXT,question_url TEXT,question_text TEXT, question_num INTEGER ," \
                  "answer_name TEXT, answer_url TEXT, answer_time TEXT, answer_text TEXT, dianzan_num INTEGER , comment_num INTEGER ," \
                  "answer_hash TEXT, spi_date TEXT)"
            self.cu.execute(sql3)
            self.con.commit()
            sql4 = "CREATE TABLE IF NOT EXISTS zhihuQuestion(keyword TEXT,question_url TEXT,question_text TEXT, question_num INTEGER ," \
                  "question_guanzhu INTEGER , question_read INTEGER , count_answer INTEGER , question_hash TEXT, spi_date TEXT)"
            self.cu.execute(sql4)
            self.con.commit()
        self.con.close()


    def table_double_clicked(self, table, index):
        table_column = index.column()
        table_row = index.row()
        current_item = table.model().index(table_row, table_column).data()
        current_table_index = self.TB.currentIndex()
        self.showFullText = showFullText(self)
        self.showFullText.setMinimumSize(700, 450)
        self.fullTextSignal.connect(self.showFullText.showText)
        self.fullTextSignal.emit(current_table_index, table_column, table_row, str(current_item))
        self.showFullText.saveSignal.connect(self.saveData)
        self.showFullText.show()
        self.fullTextSignal.disconnect(self.showFullText.showText)
        #print(table_column)


    def saveData(self, current_table_index, table_column, table_row, data):
        if current_table_index == 0:
            model = self.model
            tb = self.table
            int_list = [3, 8, 9]
            if table_column in int_list:
                data = int(data)
        elif current_table_index == 1:
            model = self.model2
            tb = self.table2
            int_list = [3, 4, 5, 6]
            if table_column in int_list:
                data = int(data)
        elif current_table_index == 2:
            tb = self.table3
            model = self.model3
        else:
            tb = self.table4
            model = self.model4
        model.setData(model.index(table_row, table_column), data)
        print(model.submitAll(), table_row, table_column, data)
        QMessageBox.information(self, '提示', '保存成功！')
        self.showFullText.close()

        model.select()
        tb.setModel(model)
        # self.showFullText.saveSignal.disconnect(self.saveData)


    def tb_reset(self, TB, table1, table2, table3, table4):
        TB.clear()
        table1.doubleClicked.connect(lambda: self.table_double_clicked(table1, table1.currentIndex()))
        table1.hideColumn(10)
        table2.doubleClicked.connect(lambda: self.table_double_clicked(table2, table2.currentIndex()))
        table2.hideColumn(7)
        table3.doubleClicked.connect(lambda: self.table_double_clicked(table3, table3.currentIndex()))
        table4.doubleClicked.connect(lambda: self.table_double_clicked(table4, table4.currentIndex()))
        TB.addTab(table1, '知乎回答')
        TB.addTab(table2, '知乎问题')
        TB.addTab(table3, '百度百家号')
        TB.addTab(table4, '新浪新闻')
        TB.show()



    def layout_init(self):
        self.st.resize(30, 15)
        self.ad.resize(30, 15)
        self.dl.resize(30, 15)
        self.rn.resize(30, 15)

        self.h_layout.addWidget(self.TB)
        self.h_layout2.addWidget(self.label2)
        self.h_layout2.addWidget(self.inpt)

        self.h_layout4.addWidget(self.label4)
        self.h_layout4.addWidget(self.spinbox)
        self.h_layout3.addWidget(self.label3)
        self.h_layout3.addWidget(self.checkbox1)
        self.h_layout3.addWidget(self.checkbox2)
        self.h_layout3.addWidget(self.checkbox3)
        self.h_layout4.setAlignment(Qt.AlignCenter)
        self.h_ad_dl.addWidget(self.ad)
        self.h_ad_dl.addWidget(self.dl)
        self.h_ad_dl.addWidget(self.rn)
        self.h_ad_dl.addWidget(self.sets)
        self.v_layout.addLayout(self.h_layout)
        self.v_layout.addLayout(self.h_ad_dl)
        # self.v_layout.addWidget(self.label1)
        # self.v_layout.addWidget(self.label5)
        # self.v_layout.addWidget(self.label6)
        self.h_start_finish.addWidget(self.label1, 0, 0)
        self.h_start_finish.addWidget(self.label_zhi_finish, 0, 1)
        self.h_start_finish.addWidget(self.label5, 1, 0)
        self.h_start_finish.addWidget(self.label_baidu_finish, 1, 1)
        self.h_start_finish.addWidget(self.label6, 2, 0)
        self.h_start_finish.addWidget(self.label_sina_finish, 2, 1)
        self.v_layout.addLayout(self.h_start_finish)
        self.h_layout2.addLayout(self.h_layout4)
        self.v_layout.addLayout(self.h_layout2)
        #self.v_layout.addLayout(self.h_layout4)
        self.v_layout.addLayout(self.h_layout3)
        self.v_layout.addWidget(self.st)
        self.setLayout(self.v_layout)
        # self.dialog_init()




    def set_buttton_disabled(self):
        self.st.setDisabled(True)
        self.ad.setDisabled(True)
        self.dl.setDisabled(True)
        self.rn.setDisabled(True)



    def closeEvent(self, QCloseEvent):
        if self.db is not None:
            self.db.close()
        #sys.exit(0)

    def sql_exec(self):

        self.model.setTable('zhihu')
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        # model = QSqlQueryModel()
        # model.setQuery("SELECT * FROM zhihu")
        self.model.setHeaderData(0, Qt.Horizontal, '检索词')
        self.model.setHeaderData(1, Qt.Horizontal, '问题url')
        self.model.setHeaderData(2, Qt.Horizontal, '问题')
        self.model.setHeaderData(3, Qt.Horizontal, '问题ID')
        self.model.setHeaderData(4, Qt.Horizontal, '回答者')
        self.model.setHeaderData(5, Qt.Horizontal, '回答url')
        self.model.setHeaderData(6, Qt.Horizontal, '回答时间')
        self.model.setHeaderData(7, Qt.Horizontal, '回答正文')
        self.model.setHeaderData(8, Qt.Horizontal, '点赞数')
        self.model.setHeaderData(9, Qt.Horizontal, '评论数')
        self.model.setHeaderData(10, Qt.Horizontal, 'hash值')
        self.model.setHeaderData(11, Qt.Horizontal, '爬取时间')
        #model.submit()
        self.model.select()

        self.table.setModel(self.model)


        self.model2.setTable('zhihuQuestion')
        self.model2.setEditStrategy(QSqlTableModel.OnFieldChange)
        # model2 = QSqlQueryModel()
        # model2.setQuery("SELECT * FROM zhihuQuestion")
        self.model2.setHeaderData(0, Qt.Horizontal, '检索词')
        self.model2.setHeaderData(1, Qt.Horizontal, '问题url')
        self.model2.setHeaderData(2, Qt.Horizontal, '问题')
        self.model2.setHeaderData(3, Qt.Horizontal, '问题ID')
        self.model2.setHeaderData(4, Qt.Horizontal, '问题关注量')
        self.model2.setHeaderData(5, Qt.Horizontal, '问题浏览量')
        self.model2.setHeaderData(6, Qt.Horizontal, '回答数量')
        self.model2.setHeaderData(7, Qt.Horizontal, 'hash值')
        self.model2.setHeaderData(8, Qt.Horizontal, '爬取时间')
        #model2.submit()
        self.model2.select()

        self.table2.setModel(self.model2)


        self.model3.setTable('baijiahao')
        self.model3.setEditStrategy(QSqlTableModel.OnFieldChange)
        # model3 = QSqlQueryModel()
        # model3.setQuery("SELECT * FROM baijiahao")
        self.model3.setHeaderData(0, Qt.Horizontal, '检索词')
        self.model3.setHeaderData(1, Qt.Horizontal, '文章url')
        self.model3.setHeaderData(2, Qt.Horizontal, '文章标题')
        self.model3.setHeaderData(3, Qt.Horizontal, '作者姓名')
        self.model3.setHeaderData(4, Qt.Horizontal, '发表时间')
        self.model3.setHeaderData(5, Qt.Horizontal, '来源')
        self.model3.setHeaderData(6, Qt.Horizontal, '正文')
        self.model3.setHeaderData(7, Qt.Horizontal, '爬取时间')
        #model3.submit()

        self.model3.select()

        self.table3.setModel(self.model3)

        # model4 = QSqlQueryModel()  # 1

        self.model4.setTable('sinanews')
        # model4.setQuery("SELECT * FROM sinanews")
        self.model4.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.model4.setHeaderData(0, Qt.Horizontal, '检索词')
        self.model4.setHeaderData(1, Qt.Horizontal, '文章url')
        self.model4.setHeaderData(2, Qt.Horizontal, '文章标题')
        self.model4.setHeaderData(3, Qt.Horizontal, '来源')
        self.model4.setHeaderData(4, Qt.Horizontal, '发表时间')
        self.model4.setHeaderData(5, Qt.Horizontal, '正文')
        self.model4.setHeaderData(6, Qt.Horizontal, '爬取时间')
        #model4.submit()

        self.model4.select()

        self.table4.setModel(self.model4)
        # QApplication.processEvents()

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table.resizeColumnsToContents()
        # self.table.resizeRowsToContents()
        self.table2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table3.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table4.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def checkbox_init(self):
        # self.checkbox1.setChecked(False)  # 1
        # self.checkbox1.setCheckState(Qt.Checked)
        self.checkbox1.stateChanged.connect(lambda: self.on_state_change_func(self.checkbox1))

    def on_state_change_func(self, checkbox):  # 6
        print('{} was clicked, and its current state is {}'.format(checkbox.text(), checkbox.checkState()))

    def button_init(self):

        self.st.clicked.connect(self.start_stop_crwal)
        self.ad.clicked.connect(self.add_line)
        self.dl.clicked.connect(self.del_line)
        self.rn.clicked.connect(self.refresh_line)


    def refresh_line(self):
        if self.TB.currentIndex() == 0:
            mdl = self.model
            tb = self.table
        elif self.TB.currentIndex() == 1:
            mdl = self.model2
            tb = self.model2
        elif self.TB.currentIndex() == 2:
            mdl = self.model3
            tb = self.table3
        else:
            mdl = self.model4
            tb = self.table4
        if mdl:
            QMessageBox.information(self, '提示', '刷新成功！')
            mdl.select()

    def add_line(self):
        if self.TB.currentIndex() == 0:
            mdl = self.model
            tb = self.table
        elif self.TB.currentIndex() == 1:
            mdl = self.model2
            tb = self.model2
        elif self.TB.currentIndex() == 2:
            mdl = self.model3
            tb = self.table3
        else:
            mdl = self.model4
            tb = self.table4
        if mdl:
            row = mdl.rowCount()
            mdl.insertRow(row)
            index = mdl.index(row, 1)
            tb.setCurrentIndex(index)
            tb.edit(index)

    def del_line(self):
        if self.TB.currentIndex() == 0:
            mdl = self.model
            tb = self.table
        elif self.TB.currentIndex() == 1:
            mdl = self.model2
            tb = self.model2
        elif self.TB.currentIndex() == 2:
            mdl = self.model3
            tb = self.table3
        else:
            mdl = self.model4
            tb = self.table4
        if mdl:
            index = tb.currentIndex()
            if not index.isValid():
                QMessageBox.information(self, 'Error', 'invalid index!')
                return
            if (QMessageBox.question(self, "Reference Data",
                                     "Are you sure to delete?",
                                     QMessageBox.Yes | QMessageBox.No) == QMessageBox.No):
                return
            mdl.removeRow(index.row())
            mdl.submitAll()
            mdl.select()

    def start_stop_crwal(self):
        if self.st.text() == '开始':
            # self.db.close()
            self.st.setText("停止")

            keyword = self.inpt.text().strip()

            if self.checkbox1.checkState() == 2:
                self.spider_list.append(TmpSpider)
                self.label1.setText("知乎收集器")
                self.label_zhi_finish.setText("正在收集")
            if self.checkbox2.checkState() == 2:
                self.spider_list.append(BaijiahaoSpider)
                self.label5.setText("百度百家号收集器")
                self.label_baidu_finish.setText("正在收集")
            if self.checkbox3.checkState() == 2:
                self.spider_list.append(SinanewsSpider)
                self.label6.setText("新浪新闻收集器")
                self.label_sina_finish.setText("正在收集")
            pages = self.spinbox.value()
            self.p = Process(target=crawl.crawl, args=(self.Q, self.spider_list, keyword, pages, self.hostname, self.dbname, self.username, self.pwd))
            # self.spider_list=[]
            self.p.start()
            #self.p.join()
            self.log_thread.start()
        else:
            self.p.terminate()
            self.log_thread.terminate()
            self.spider_list = []
            if self.checkbox1.checkState() == 2:
                self.label1.setText("知乎收集器")
                self.label_zhi_finish.setText("就绪")
            if self.checkbox2.checkState() == 2:
                self.label5.setText("百度百家号收集器")
                self.label_baidu_finish.setText("就绪")
            if self.checkbox3.checkState() == 2:
                self.label6.setText("新浪新闻收集器")
                self.label_sina_finish.setText("就绪")
            # self.db_connect()
            # self.sql_exec()
            self.st.setText("开始")

def res_path(relative_path):
    """获取资源绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class LDAThread(QThread):
    running_signal =pyqtSignal(str)
    finish_signal = pyqtSignal(list, list)
    def __init__(self):
        super(LDAThread, self).__init__()
        manager = Manager()
        self.return_dict = manager.dict()
        self.count = 0

    def save_data(self, text_list, lda_topic_num, lda_turns_num):
        self.text_list = text_list
        self.lda_topic_num = lda_topic_num
        self.lda_turns_num = lda_turns_num

    def run(self):
        self.p = Process(target=textPro.LDA, args=(self.text_list, self.lda_topic_num, self.lda_turns_num, self.return_dict))
        self.p.start()
        while self.p.is_alive():
            s = '正在处理' + self.count % 4 * '.'
            self.count = self.count + 1
            self.sleep(1)
            self.running_signal.emit(s)

        self.finish_signal.emit(self.return_dict.values()[0], self.return_dict.values()[1].tolist())



class lda_dialog(QDialog):
    getText_signal = pyqtSignal(int)
    lda_start_signal = pyqtSignal(list, int, int)
    def __init__(self, parent=None):
        super(lda_dialog, self).__init__(parent)
        self.zhihu_list = ['问题', '回答正文', '问题+回答正文']
        self.zhiques_list = ['问题']
        self.bai_list = ['文章标题', '正文', '文章标题+正文']
        self.sina_list = ['文章标题', '正文', '文章标题+正文']

        self.setMinimumSize(500, 700)
        self.setWindowTitle('LDA主题分析')
        self.setWindowModality(Qt.ApplicationModal)
        self.content_label = QLabel('LDA分析内容：', self)
        self.topic_num_label = QLabel('LDA预计主题数：', self)
        self.turns_label = QLabel('LDA训练轮数：', self)
        self.content_combox = QComboBox(self)
        self.topic_spinbox = QSpinBox(self)
        self.topic_spinbox.setRange(1, 100)  # 1
        self.topic_spinbox.setSingleStep(1)  # 2
        self.topic_spinbox.setValue(1)

        self.turns_spinbox = QSpinBox(self)
        self.turns_spinbox.setRange(100, 3000)  # 1
        self.turns_spinbox.setSingleStep(100)  # 2
        self.turns_spinbox.setValue(100)

        self.startlda_btn = QPushButton('开始', self)
        self.quit_btn = QPushButton('取消', self)
        self.startlda_btn.clicked.connect(self.run_lda)
        self.quit_btn.clicked.connect(self.close)
        self.topic_label = QLabel('话题关键词：', self)
        self.infer_label = QLabel('文档主题推测：', self)
        self.topic_broswer = QTextBrowser(self)
        self.infer_broswer = QTextBrowser(self)

        self.ldaThread = LDAThread()

        self.text_list = []
        self.h_lyt = QHBoxLayout()
        self.f_lyt = QFormLayout()
        self.v_lyt = QVBoxLayout()
        self.lda_dialog_layout_init()

    def lda_process(self, com1, com2):
        self.com1 = com1
        self.com2 = com2
        self.content_combox.clear()
        if self.com1 == 0:
            self.content_combox.addItems(self.zhihu_list)
        elif self.com1 == 1:
            self.content_combox.addItems(self.zhiques_list)
        elif self.com1 == 2:
            self.content_combox.addItems(self.bai_list)
        else:
            self.content_combox.addItems(self.sina_list)
        self.show()


    def lda_dialog_layout_init(self):


        self.f_lyt.addRow(self.content_label, self.content_combox)
        self.f_lyt.addRow(self.topic_num_label, self.topic_spinbox)
        self.f_lyt.addRow(self.turns_label, self.turns_spinbox)

        self.h_lyt.addWidget(self.startlda_btn)
        self.h_lyt.addWidget(self.quit_btn)

        self.v_lyt.addLayout(self.f_lyt)
        self.v_lyt.addLayout(self.h_lyt)
        self.v_lyt.addWidget(self.topic_label)
        self.v_lyt.addWidget(self.topic_broswer)
        self.v_lyt.addWidget(self.infer_label)
        self.v_lyt.addWidget(self.infer_broswer)

        self.setLayout(self.v_lyt)

    def run_lda(self):
        text_list = []
        self.startlda_btn.setDisabled(True)
        table_num = self.com1
        content_num = self.content_combox.currentIndex()
        self.getText_signal.emit(content_num)
        # self.text_list = self.get_lda_text(table_num, content_num)
        lda_topic_num = self.topic_spinbox.value()
        lda_turns_num = self.turns_spinbox.value()

        self.lda_start_signal.connect(self.ldaThread.save_data)
        self.lda_start_signal.emit(self.text_list, lda_topic_num, lda_turns_num)
        self.lda_start_signal.disconnect(self.ldaThread.save_data)
        self.ldaThread.running_signal.connect(self.set_running_lda)
        self.ldaThread.finish_signal.connect(self.finish_lda)
        self.ldaThread.start()


    def set_running_lda(self, txt):
        self.startlda_btn.setText(txt)

    def finish_lda(self, topics, probs):
        self.startlda_btn.setText('开始')
        self.startlda_btn.setEnabled(True)
        topic_show = []
        for i, item in enumerate(topics):
            topic_show.append('话题{}：{}'.format(i + 1, item[1]))
        self.topic_broswer.setText('\n\n'.join(topic_show))
        infer_show = []
        for i, item in enumerate(probs):
            belong_to = item.index(max(item)) + 1
            infer_show.append('文档{}：话题{}'.format(i + 1, belong_to))
        self.infer_broswer.setText('\n'.join(infer_show))

    def closeEvent(self, QCloseEvent):
        if self.ldaThread.isRunning():
            self.ldaThread.exit()
        self.close()


class LDAWidget(QWidget):
    tab_list = ['知乎回答', '知乎问题', '百度百家号', '新浪新闻']
    tab_name = ['zhihu', 'zhihuQuestion', 'baijiahao', 'sinanews']

    def __init__(self):
        super(LDAWidget, self).__init__()
        self.tab_label = QLabel('检索表格：', self)
        self.title_label = QLabel('检索字段：', self)
        self.info_label = QLabel('', self)
        self.combobox_1 = QComboBox(self)
        self.combobox_1.setDisabled(True)
        self.combobox_2 = QComboBox(self)
        self.combobox_2.setDisabled(True)
        self.sel_table = QTableView(self)

        self.search_btn = QPushButton('查询', self)
        self.search_btn.setDisabled(True)
        self.search_btn.setFixedSize(200, 50)

        self.lda_btn = QPushButton('LDA分析', self)
        self.lda_btn.setDisabled(True)
        self.lda_btn.setFixedSize(200, 50)
        self.lda_btn.hide()

        self.combobox_init()
        self.f_layout = QFormLayout()
        self.h_layout = QHBoxLayout()
        self.v_layout = QVBoxLayout()

        self.btn_init()
        self.layout_init()

    def btn_init(self):
        com1 = self.combobox_1.currentIndex()
        com2 = self.combobox_2.currentIndex()

        self.search_btn.clicked.connect(self.show_data)
        self.lda_btn.clicked.connect(lambda: self.lda_dlog_init(com1, com2))

    def lda_dlog_init(self, com1, com2):
        self.lda_dlog = lda_dialog(self)
        self.lda_dlog.getText_signal.connect(self.get_lda_text)
        self.lda_dlog.lda_process(com1, com2)

    def show_data(self):
        self.model1 = QSqlTableModel()
        self.model1.setTable(self.tab_name[self.combobox_1.currentIndex()])
        self.sql_exec(self.combobox_1.currentIndex())
        self.model1.setFilter('keyword=\"{}\"'.format(self.combobox_2.currentText()))
        print("keyword=\"{}\"".format(self.combobox_2.currentText()))
        self.sel_table.setModel(self.model1)
        index_table = self.combobox_1.currentIndex()
        if index_table == 0:
            self.sel_table.showColumn(7)
            self.sel_table.hideColumn(10)
        elif index_table == 1:
            self.sel_table.hideColumn(7)
        else:
            self.sel_table.showColumn(7)
        self.model1.select()
        self.sel_count = self.model1.rowCount()
        self.info_label.setText('共得到{}条记录。'.format(str(self.sel_count)))
        self.lda_btn.show()
        if self.sel_count != 0:
            self.lda_btn.setEnabled(True)

    def get_lda_text(self, content_num):
        text_list = []
        table_num = self.combobox_1.currentIndex()
        if table_num == 0:
            if content_num == 0:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('question_text')
                    text_list.append(text)
            elif content_num == 1:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('answer_text')
                    text_list.append(text)
            elif content_num == 2:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('question_text') + self.model1.record(i).value('answer_text')
                    text_list.append(text)
        elif table_num == 1:
            if content_num == 0:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('question_text')
                    text_list.append(text)
        elif table_num == 2:
            if content_num == 0:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('article_title')
                    text_list.append(text)
            elif content_num == 1:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('article_text')
                    text_list.append(text)
            elif content_num == 2:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('article_title') + self.model1.record(i).value('article_text')
                    text_list.append(text)
        elif table_num == 3:
            if content_num == 0:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('article_title')
                    text_list.append(text)
            elif content_num == 1:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('article_text')
                    text_list.append(text)
            elif content_num == 2:
                for i in range(self.model1.rowCount()):
                    text = self.model1.record(i).value('article_title') + self.model1.record(i).value('article_text')
                    text_list.append(text)

        self.lda_dlog.text_list = [t.replace(' ', '') for t in text_list]
        self.lda_dlog.getText_signal.disconnect(self.get_lda_text)

    def layout_init(self):
        self.f_layout.addRow(self.tab_label, self.combobox_1)
        self.f_layout.addRow(self.title_label, self.combobox_2)

        self.h_layout.addWidget(self.info_label)
        self.h_layout.addWidget(self.lda_btn, alignment=Qt.AlignRight)
        self.h_layout.addWidget(self.search_btn, alignment=Qt.AlignRight)

        self.v_layout.addLayout(self.f_layout)
        self.v_layout.addLayout(self.h_layout)
        self.v_layout.addWidget(self.sel_table)
        self.setLayout(self.v_layout)

    def combobox_init(self):
        self.combobox_1.addItems(self.tab_list)
        self.combobox_1.currentIndexChanged.connect(lambda: self.on_combobox_func(self.combobox_1))
        self.combobox_2.currentIndexChanged.connect(lambda: self.on_combobox_func(self.combobox_2))

    def on_combobox_func(self, combobox):  # 8
        if combobox == self.combobox_1:
            # QMessageBox.information(self, 'ComboBox 1',
            #                         '{}: {}'.format(combobox.currentIndex(), combobox.currentText()))
            self.setComChange(combobox, self.combobox_2)
        else:
            pass
        self.lda_btn.setDisabled(True)

    def setComChange(self, combobox_a, combobox_b):
        model = QSqlQueryModel()  # 1
        model.setQuery("SELECT keyword FROM {}".format(self.tab_name[combobox_a.currentIndex()]))
        keyword_list = []
        for i in range(model.rowCount()):  # 3
            keyword = model.record(i).value('keyword')
            keyword_list.append(keyword)
        combobox_b.clear()
        combobox_b.addItems(set(keyword_list))
        combobox_b.setEnabled(True)

    def sql_exec(self, index):

        if index == 0:
            # self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
            # model = QSqlQueryModel()
            # model.setQuery("SELECT * FROM zhihu")
            # self.sel_table.hideColumn(10)
            self.model1.setHeaderData(0, Qt.Horizontal, '检索词')
            self.model1.setHeaderData(1, Qt.Horizontal, '问题url')
            self.model1.setHeaderData(2, Qt.Horizontal, '问题')
            self.model1.setHeaderData(3, Qt.Horizontal, '问题ID')
            self.model1.setHeaderData(4, Qt.Horizontal, '回答者')
            self.model1.setHeaderData(5, Qt.Horizontal, '回答url')
            self.model1.setHeaderData(6, Qt.Horizontal, '回答时间')
            self.model1.setHeaderData(7, Qt.Horizontal, '回答正文')
            self.model1.setHeaderData(8, Qt.Horizontal, '点赞数')
            self.model1.setHeaderData(9, Qt.Horizontal, '评论数')
            self.model1.setHeaderData(10, Qt.Horizontal, 'hash值')
            self.model1.setHeaderData(11, Qt.Horizontal, '爬取时间')
            #model.submit()


            # self.table.setModel(self.model)

        elif index == 1:
            # self.model2.setTable('zhihuQuestion')
            # self.model2.setEditStrategy(QSqlTableModel.OnFieldChange)
            # model2 = QSqlQueryModel()
            # model2.setQuery("SELECT * FROM zhihuQuestion")
            self.model1.setHeaderData(0, Qt.Horizontal, '检索词')
            self.model1.setHeaderData(1, Qt.Horizontal, '问题url')
            self.model1.setHeaderData(2, Qt.Horizontal, '问题')
            self.model1.setHeaderData(3, Qt.Horizontal, '问题ID')
            self.model1.setHeaderData(4, Qt.Horizontal, '问题关注量')
            self.model1.setHeaderData(5, Qt.Horizontal, '问题浏览量')
            self.model1.setHeaderData(6, Qt.Horizontal, '回答数量')
            self.model1.setHeaderData(7, Qt.Horizontal, 'hash值')
            self.model1.setHeaderData(8, Qt.Horizontal, '爬取时间')
            #model2.submit()
            # self.model1.select()
            # self.sel_table.hideColumn(7)

            # self.table2.setModel(self.model2)

        elif index == 2:
            # self.model3.setTable('baijiahao')
            # self.model3.setEditStrategy(QSqlTableModel.OnFieldChange)
            # model3 = QSqlQueryModel()
            # model3.setQuery("SELECT * FROM baijiahao")
            self.model1.setHeaderData(0, Qt.Horizontal, '检索词')
            self.model1.setHeaderData(1, Qt.Horizontal, '文章url')
            self.model1.setHeaderData(2, Qt.Horizontal, '文章标题')
            self.model1.setHeaderData(3, Qt.Horizontal, '作者姓名')
            self.model1.setHeaderData(4, Qt.Horizontal, '发表时间')
            self.model1.setHeaderData(5, Qt.Horizontal, '来源')
            self.model1.setHeaderData(6, Qt.Horizontal, '正文')
            self.model1.setHeaderData(7, Qt.Horizontal, '爬取时间')
            #model3.submit()

            # self.model3.select()

            # self.table3.setModel(self.model3)

        else:
            # model4 = QSqlQueryModel()  # 1

            # self.model4.setTable('sinanews')
            # model4.setQuery("SELECT * FROM sinanews")
            # self.model4.setEditStrategy(QSqlTableModel.OnFieldChange)
            self.model1.setHeaderData(0, Qt.Horizontal, '检索词')
            self.model1.setHeaderData(1, Qt.Horizontal, '文章url')
            self.model1.setHeaderData(2, Qt.Horizontal, '文章标题')
            self.model1.setHeaderData(3, Qt.Horizontal, '来源')
            self.model1.setHeaderData(4, Qt.Horizontal, '发表时间')
            self.model1.setHeaderData(5, Qt.Horizontal, '正文')
            self.model1.setHeaderData(6, Qt.Horizontal, '爬取时间')
            #model4.submit()

            # self.model4.select()

            # self.table4.setModel(self.model4)
            # QApplication.processEvents()

        self.sel_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table.resizeColumnsToContents()
        # self.table.resizeRowsToContents()
        # self.table2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table3.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.table4.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

class Demo(QMainWindow):
    def __init__(self):
        super(Demo, self).__init__()
        self.setWindowTitle('数据收集分析器')
        self.TB = QTabWidget(self)
        self.spiderWidget = DemoWidget()
        self.table_init()
        self.spiderWidget.TB.addTab(self.spiderWidget.table, '知乎回答')
        self.spiderWidget.TB.addTab(self.spiderWidget.table2, '知乎问题')
        self.spiderWidget.TB.addTab(self.spiderWidget.table3, '百度百家号')
        self.spiderWidget.TB.addTab(self.spiderWidget.table4, '新浪新闻')
        self.spiderWidget.layout_init()
        self.dialog_init()
        self.spiderWidget.sets.clicked.connect(self.dialog_init)
        self.TB.addTab(self.spiderWidget, '数据收集')
        self.ldaWidget = LDAWidget()
        self.TB.addTab(self.ldaWidget, '检索与主题分析')
        self.setCentralWidget(self.TB)
        self.resize(1000, 500)
        self.setWindowIcon(QIcon(res_path('icon2.ico')))
        self.db = None

    def dialog_init(self):
        self.login = Dialog(self.spiderWidget)
        self.login.setWindowModality(Qt.ApplicationModal)
        self.login.show()
        self.login.activateWindow()
        self.login.dialogSignel.connect(self.input_info)

    @pyqtSlot(int, str, str, str, str)
    def input_info(self, count, hostname, dbname, username, pwd):
        self.hostname = hostname
        self.dbname = dbname
        self.username = username
        self.pwd = pwd
        self.spiderWidget.hostname = hostname
        self.spiderWidget.dbname = dbname
        self.spiderWidget.username = username
        self.spiderWidget.pwd = pwd
        self.db_connect(count, hostname, dbname, username, pwd)
        self.ldaWidget.combobox_1.setEnabled(True)
        self.ldaWidget.search_btn.setEnabled(True)
        self.ldaWidget.setComChange(self.ldaWidget.combobox_1, self.ldaWidget.combobox_2)
        self.login.login_button.clicked.disconnect(self.login.check)

    def db_connect(self, count, hostname, dbname, username, pwd):
        self.spiderWidget.database_init()
        if self.db is not None:
            self.spiderWidget.table_z1 = QTableView(self)
            self.spiderWidget.table_z2 = QTableView(self)
            self.spiderWidget.table_z3 = QTableView(self)
            self.spiderWidget.table_z4 = QTableView(self)
            self.spiderWidget.tb_reset(self.spiderWidget.TB, self.spiderWidget.table_z1, self.spiderWidget.table_z2, self.spiderWidget.table_z3, self.spiderWidget.table_z4)
            self.spiderWidget.set_buttton_disabled()
        #


        if self.db is not None and self.db.contains('qt_sql_default_connection'):
            self.db = QSqlDatabase.database('qt_sql_default_connection')
        else:
            self.db = QSqlDatabase.addDatabase('QMYSQL')

        self.db.setHostName(hostname)
        self.db.setDatabaseName(dbname)
        self.db.setUserName(username)
        self.db.setPassword(pwd)

        # query = QSqlQuery()
        # query.exec_("CREATE DATABASE IF NOT EXISTS {}".format(self.dbname))

        if not self.db.open():
            QMessageBox.critical(self, 'Database Connection', self.db.lastError().text())
            self.login.login_button.clicked.connect(self.login.check)
        else:
            print(count)
            QMessageBox.information(self, '提示', '连接成功！')
            self.spiderWidget.TB.close()
            self.table_init()
            self.spiderWidget.sql_exec()
            self.spiderWidget.tb_reset(self.spiderWidget.TB, self.spiderWidget.table, self.spiderWidget.table2, self.spiderWidget.table3, self.spiderWidget.table4)
            self.login.close()
            self.spiderWidget.st.setEnabled(True)
            self.spiderWidget.rn.setEnabled(True)
            self.spiderWidget.ad.setEnabled(True)
            self.spiderWidget.dl.setEnabled(True)

    def table_init(self):

        self.spiderWidget.table = QTableView(self)
        self.spiderWidget.table.setSortingEnabled(True)
        self.spiderWidget.table2 = QTableView(self)
        self.spiderWidget.table3 = QTableView(self)
        self.spiderWidget.table4 = QTableView(self)
        self.spiderWidget.table2.setSortingEnabled(True)
        self.spiderWidget.table3.setSortingEnabled(True)
        self.spiderWidget.table4.setSortingEnabled(True)
        self.spiderWidget.model = QSqlTableModel()  # 1
        self.spiderWidget.model2 = QSqlTableModel()  # 1
        self.spiderWidget.model3 = QSqlTableModel()  # 1
        self.spiderWidget.model4 = QSqlTableModel()  # 1

    #def db(self):


if __name__ == '__main__':
    app = QApplication(sys.argv)
    splash = QSplashScreen()
    splash.setPixmap(QPixmap(res_path('start2.png')))
    splash.show()
    splash.showMessage('Welcome to use Jisi!', Qt.AlignBottom | Qt.AlignCenter, Qt.darkYellow)
    demo = Demo()
    demo.show()
    splash.finish(demo)
    sys.exit(app.exec_())
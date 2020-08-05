import sys
from PyQt5.QtCore import Qt
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableView, QWidget, QLabel, QVBoxLayout, QHBoxLayout, \
    QHeaderView, QLineEdit, QPushButton, QCheckBox, QGridLayout, QComboBox, QTabWidget, QSpinBox, QSplitter
from PyQt5.QtCore import QThread, pyqtSignal, QFile, QTextStream
from baiduCrawler.spiders.tmp import TmpSpider
from baiduCrawler.spiders.baijiahao import  BaijiahaoSpider
from baiduCrawler.spiders.sinanews import SinanewsSpider
from multiprocessing import Process, Manager, JoinableQueue
import ctypes
import scrapy
from scrapy.crawler import CrawlerProcess
import logging


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


def crawl(Q, spider_list, keyword, pages):
    # CrawlerProcess
    process = CrawlerProcess()
    #Q.clear()
    for spi in spider_list:
        process.crawl(spi, Q=Q, keywords=keyword, pages=pages)
    process.start()


class Demo(QWidget):
    def __init__(self):
        super(Demo, self).__init__()
        self.setWindowTitle('数据收集器')
        self.db = None
        self.db_connect()
        self.resize(1000, 500)
        #self.crawl_thread = CrawlThread(self)
        self.table = QTableView(self)
        self.table.setSortingEnabled(True)
        self.table2 = QTableView(self)
        self.table3 = QTableView(self)
        self.table4 = QTableView(self)
        self.table2.setSortingEnabled(True)
        self.table3.setSortingEnabled(True)
        self.table4.setSortingEnabled(True)


        self.login = QWidget(self)
        self.login.setWindowTitle('连接数据库')
        self.hostname_label = QLabel('Host name:', self.login)
        self.database_label = QLabel('Database name:', self.login)
        self.user_label = QLabel('Username:', self.login)
        self.pwd_label = QLabel('Password:', self.login)




        #self.table3 = QTableView(self)
        self.TB = QTabWidget(self)
        self.model = QSqlTableModel()  # 1
        self.model2 = QSqlTableModel()  # 1
        self.model3 = QSqlTableModel()  # 1
        self.model4 = QSqlTableModel()  # 1
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
        self.sql_exec()
        self.TB.addTab(self.table, '知乎回答')
        self.TB.addTab(self.table2, '知乎问题')
        self.TB.addTab(self.table3, '百度百家号')
        self.TB.addTab(self.table4, '新浪新闻')
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
        self.layout_init()
        #self.checkbox_init()
        self.button_init()

    #def login_init(self):


    def layout_init(self):
        self.st.resize(30, 15)
        self.ad.resize(30, 15)
        self.dl.resize(30, 15)
        self.rn.resize(30, 15)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table3.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table4.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

    def db_connect(self):
        self.db = QSqlDatabase.addDatabase('QMYSQL')
        self.db.setHostName('localhost')
        self.db.setDatabaseName('NEWSDB')
        self.db.setUserName('root')
        self.db.setPassword('150827')
        if not self.db.open():
            QMessageBox.critical(self, 'Database Connection', self.db.lastError().text())

    def closeEvent(self, QCloseEvent):
        self.db.close()

    def sql_exec(self):

        self.model.setTable('zhihu')
        self.model.setEditStrategy(QSqlTableModel.OnFieldChange)
        # model = QSqlQueryModel()
        # model.setQuery("SELECT * FROM zhihu")
        self.model.setHeaderData(0, Qt.Horizontal, '关键词')
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
        self.model2.setHeaderData(0, Qt.Horizontal, '关键词')
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
        self.model3.setHeaderData(0, Qt.Horizontal, '关键词')
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
        self.model4.setHeaderData(0, Qt.Horizontal, '关键词')
        self.model4.setHeaderData(1, Qt.Horizontal, '文章url')
        self.model4.setHeaderData(2, Qt.Horizontal, '文章标题')
        self.model4.setHeaderData(3, Qt.Horizontal, '来源')
        self.model4.setHeaderData(4, Qt.Horizontal, '发表时间')
        self.model4.setHeaderData(5, Qt.Horizontal, '正文')
        self.model4.setHeaderData(6, Qt.Horizontal, '爬取时间')
        #model4.submit()

        self.model4.select()

        self.table4.setModel(self.model4)

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
            self.p = Process(target=crawl, args=(self.Q, self.spider_list, keyword, pages))
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




if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = Demo()
    demo.show()
    sys.exit(app.exec_())
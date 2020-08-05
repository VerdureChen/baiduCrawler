# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class BaiducrawlerSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class BaiducrawlerDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def click_locxy(self, br, x, y, left_click=True):
        if left_click:
            ActionChains(br).move_by_offset(x, y).click().perform()
        else:
            ActionChains(br).move_by_offset(x, y).context_click().perform()
        ActionChains(br).move_by_offset(-x, -y).click().perform()

    def is_element_present(self, driver, how, what):
        try:
            driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True


    def process_request(self, request, spider):
        '''
        如果是知乎url，则接入selenium
        :param request:
        :param spider:
        :return:
        '''
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        if re.match('https://www.baidu.com', request.url):
            return None
        elif re.match('(https://www.zhihu.com/question/)(\d+)', request.url):
            # desired_capabilities = DesiredCapabilities.CHROME
            # desired_capabilities["pageLoadStrategy"] = "none"
            option = webdriver.ChromeOptions()
            option.add_argument('headless')
            option.add_argument('log-level=1')
            prefs = {'profile.managed_default_content_settings.images': 2}
            option.add_experimental_option('prefs', prefs)
            br = webdriver.Chrome(chrome_options=option)
            wait = WebDriverWait(br, 20)
            wait2 = WebDriverWait(br, 10)
            br.get(request.url)

            try:
                if self.is_element_present(br, By.XPATH, './/div[@class="Card Answers-none"]'):
                    return None

                ans_num = br.find_element_by_xpath('.//h4/span').text
                s = re.search('([0-9,]+)', ans_num).group(1).replace(',','')
                if int(s) <= 20:
                    turl = re.match('(https://www.zhihu.com/question/)(\d+)', request.url)
                    tu = turl.group(1) + turl.group(2)
                    br.get(tu)
                    if self.is_element_present(br, By.XPATH, './/button[@class="Button QuestionAnswers-answerButton Button--blue Button--spread"]'):
                        pass
                    else:
                        '''
                        如果问题的回答数量少于20，则没有翻页信息，寻找‘写回答’的标签。
                        如果该问题没有回答，则不提取该页面
                        '''
                        js = "var q=document.documentElement.scrollTop=100000"
                        br.execute_script(js)
                        time.sleep(2)
                        inner = wait.until(EC.presence_of_element_located((By.XPATH, './/div[@class="Modal-inner"]')))
                        self.click_locxy(br, 100, 0)  # 左键点击
                        js = "var q=document.documentElement.scrollTop=100000"
                        br.execute_script(js)
                        time.sleep(2)
                        target = wait2.until(EC.presence_of_element_located((By.XPATH,
                                                                             './/button[@class="Button QuestionAnswers-answerButton Button--blue Button--spread"]')))
                        target.location_once_scrolled_into_view
                else:
                    if self.is_element_present(br, By.XPATH, './/div[@class="Pagination"]'):
                        pass
                    else:
                        target = wait.until(EC.presence_of_element_located((By.XPATH, './/div[@class="Pagination"]')))
                        target.location_once_scrolled_into_view
            except TimeoutException:
                return HtmlResponse(url=request.url, status=500, request=request)

            # try:
            #     # js = "var q=document.documentElement.scrollTop=100000"
            #     # br.execute_script(js)
            #     # time.sleep(2)
            #     # inner = wait.until(EC.presence_of_element_located((By.XPATH, './/div[@class="Modal-inner"]')))
            #     # self.click_locxy(br, 100, 0)  # 左键点击
            #     target = wait.until(EC.presence_of_element_located((By.XPATH, './/div[@class="Pagination"]')))
            #     target.location_once_scrolled_into_view
            # except TimeoutException:
            #     turl= re.match('(https://www.zhihu.com/question/)(\d+)',request.url)
            #     tu=turl.group(1)+turl.group(2)
            #     br.get(tu)
            #     try:
            #         '''
            #         如果问题的回答数量少于20，则没有翻页信息，寻找‘写回答’的标签。
            #         如果该问题没有回答，则不提取该页面
            #         '''
            #         js = "var q=document.documentElement.scrollTop=100000"
            #         br.execute_script(js)
            #         time.sleep(2)
            #         inner = wait.until(EC.presence_of_element_located((By.XPATH, './/div[@class="Modal-inner"]')))
            #         self.click_locxy(br, 100, 0)  # 左键点击
            #         js = "var q=document.documentElement.scrollTop=100000"
            #         br.execute_script(js)
            #         time.sleep(2)
            #         target = wait2.until(EC.presence_of_element_located((By.XPATH, './/button[@class="Button QuestionAnswers-answerButton Button--blue Button--spread"]')))
            #         target.location_once_scrolled_into_view
            #     except TimeoutException:
            #         return HtmlResponse(url=request.url, status=500, request=request)
            # html_str = br.page_source
            #br.quit()
            # inner = wait.until(EC.presence_of_element_located((By.XPATH, './/div[@class="Modal-inner"]')))
            # self.click_locxy(br, 100, 0)  # 左键点击
            return HtmlResponse(url=request.url, body=br.page_source, request=request, encoding='utf-8',
                                status=200)

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

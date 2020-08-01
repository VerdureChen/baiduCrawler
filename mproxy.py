from mitmproxy import ctx


def response(flow):
    # 'js'字符串为目标网站的相应js名
    if 'js' in flow.request.url:
        for i in ['webdriver', '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate',
                  '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped', '__selenium_unwrapped',
                  '__fxdriver_unwrapped', '_Selenium_IDE_Recorder', '_selenium', 'calledSelenium',
                  '_WEBDRIVER_ELEM_CACHE', 'ChromeDriverw', 'driver-evaluate', 'webdriver-evaluate',
                  'selenium-evaluate', 'webdriverCommand', 'webdriver-evaluate-response', '__webdriverFunc',
                  '__webdriver_script_fn', '__$webdriverAsyncExecutor', '__lastWatirAlert', '__lastWatirConfirm',
                  '__lastWatirPrompt', '$chrome_asyncScriptInfo', '$cdc_asdjflasutopfhvcZLmcfl_','callPhantom',
                  '_phantom','__phantomas','buffer','Buffer','emit','spawn', 'domAutomation'.'domAutomationController']:
            ctx.log.info('Remove %s from %s.' % (i, flow.request.url))
            flow.response.text = flow.response.text.replace('%s' % i, 'User-Agent')
        flow.response.text = flow.response.text.replace('t.webdriver', 'false')
        flow.response.text = flow.response.text.replace('ChromeDriver', '')
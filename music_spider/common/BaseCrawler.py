# coding:utf8

import base64
# 系统库
import copy
import json
import sys
import time
import traceback

import requests

# 本地库
sys.path.append('../../common')
sys.path.append('../../main')
import settings
import utils
import proxy_helper


# requests.adapters.DEFAULT_RETRIES = 1#重试一次

class BaseCrawler:
    """BaseCrawler 爬虫基类"""

    def __init__(self, threadID, logger, ttype, siteName, siteHost, proxy_type, sock, seeds,
                 limit=settings.proxy_one_time_limit, timeout=settings.openUrlTimeout, reset_session_flag=True):
        import pdb
        pdb.set_trace()
        self.threadID = threadID
        self.logger = logger
        self.ttype = ttype
        self.siteName = siteName
        self.siteHost = siteHost
        self.proxy_type = proxy_type
        self.sock = sock
        self.seeds = seeds
        self.session = requests.Session()
        self.timeout = timeout
        self.last_timestamp = int(time.time())
        self.last_crawl_count = 0
        self.total_crawl_count = 0
        self.ip = None
        self.port = None
        self.limit = limit
        self.reset_session_flag = reset_session_flag
        self.proxy_count = 0

    def run(self):
        import pdb
        pdb.set_trace()
        self.init_session()
        try:
            if hasattr(self, self.ttype):
                getattr(self, self.ttype)()
            else:
                self.logger.error('no such task type:%s' % self.ttype)
        except:
            self.logger.error(traceback.format_exc())
            utils.send_email(traceback.format_exc())

    # 新加入自动重试功能
    def openUrl(self, url, method='get', headers={}, data={}, isImg=False, timeout=settings.openUrlTimeout,
                encoding=None, headersHost=None, retries=10):
        try_times = 0
        while try_times < retries:
            if self.last_crawl_count >= self.limit and self.reset_session_flag:  # 当一个账号使用超过限制以后会换账号
                self.init_session()
            response = self._openUrl(url, method=method, headers=headers, data=data, isImg=isImg, timeout=timeout,
                                     encoding=encoding, headersHost=headersHost)
            return response

    # 自定义url opener函数
    def _openUrl(self, url, method='get', headers={}, data={}, isImg=False, timeout=settings.openUrlTimeout,
                 encoding=None, headersHost=None):
        _headers = copy.copy(headers)
        if headersHost is not None:
            _headers['Host'] = headersHost
        else:
            try:
                _headers['Host'] = url.split('//')[1].split('/')[0]
            except Exception as e:
                self.logger.error(str(e) + ' : ' + url)

        t0 = time.time()
        self.logger.debug("begin to crawl url :%s" % url)
        if self.timeout > timeout:  # 取大的超时时间
            timeout = self.timeout
        try:
            if method == 'get':
                res = self.session.get(url, headers=_headers, params=data, timeout=timeout)
            else:
                res = self.session.post(url, headers=_headers, params=data, timeout=timeout)

            self.logger.debug('status:%d, encoding:%s' % (res.status_code, res.encoding))

            if res.status_code != 200:  # http status
                self.logger.error('status:%d, encoding:%s, url:%s' % (res.status_code, res.encoding, url))
                if res.status_code == 403 and (self.proxy_type == "socks" or self.proxy_type == "http"):
                    proxy_helper.delete_proxy(isown=1, ip=self.ip, site=self.siteName)

                return None
            if encoding is not None:  # 编码
                res.encoding = encoding
            else:
                if res.encoding.lower() in ['gbk', 'gb2312', 'windows-1252']:
                    res.encoding = 'gb18030'
                elif res.encoding.lower() in ['iso-8859-1', 'iso8859-1']:
                    res.encoding = 'utf8'

            if isImg:
                response = res.content
            else:
                response = res.text
            time.sleep(settings.http_sleep_time)
        except Exception as e:
            self.logger.error('download html failed, url: ' + url + ' , error: ' + str(e))
            if (self.proxy_type == "socks" or self.proxy_type == "http"):
                proxy_helper.delete_proxy(isown=1, ip=self.ip, site=self.siteName)

            return None
        # decode to unicode
        response = utils.decodeToUnicode(response, isImg)
        t_diff = time.time() - t0
        self.logger.debug("finish to crawl url :%s, use time:%s" % (url, t_diff))
        return response

    def init_session(self):
        while True:
            self.logger.info('begin to reset session')
            self.last_crawl_count = 0
            self.session = requests.Session()
            # 建立session, get http proxy
            if self.proxy_type == "socks" or self.proxy_type == "http" or self.proxy_type == "all":
                self.reset_proxy()
            res = self.reset_account()
            if res:
                self.logger.info('reset session success')
                return
            
    def reset_account(self):
        return True

    def reset_proxy(self):
        while True:
            self.logger.info('begin to reset_proxy')
            if self.proxy_type == "http":
                proxies = proxy_helper.get_proxy(isown=1, protocol=0, site=self.siteName, count=1)
            elif self.proxy_type == "socks":
                proxies = proxy_helper.get_proxy(isown=1, protocol=1, site=self.siteName, count=1)
            else:
                proxies = proxy_helper.get_proxy(isown=1, protocol=None, site=self.siteName, count=1)

            if len(proxies) == 0:
                self.logger.warning('no proxy .....')
                time.sleep(60 * 10)
                continue
            proxy = proxies[0]
            self.logger.debug(proxy)
            self.ip = proxy['ip']
            self.port = proxy['port']
            if proxy['protocol'] == 0:
                proxies = {'http': 'http://%s:%s/' % (self.ip, self.port),
                           'https': 'http://%s:%s/' % (self.ip, self.port)
                           }
            self.session.proxies = proxies
            self.logger.info('reset_proxy success')
            self.proxy_count += 1
            print('self.proxy_count:%s...........' % self.proxy_count)
            return

    def get_value_from_xpath(self, node, xpath, default=None):
        nodes = node.xpath(xpath)
        if len(nodes):
            return nodes[0]
        else:
            return default

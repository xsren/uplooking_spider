# coding:utf8
import requests
import time
import json

FAIL_SLEEP_TIME = 10
host = 'http://47.93.254.110:8002'
token = '4cc5fbe69e2a93d48bef68319b763541'


def get_proxy(isown, protocol, site, count=1, logger=None):
    while True:
        try:
            url = '%s/select?isown=%s&protocol=%s&site=%s&token=%s&count=%s' % (
            host, isown, protocol, site, token, count)
            print(url)
            res = requests.get(url)
            return json.loads(res.text)['data']
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print(str(e))
            time.sleep(FAIL_SLEEP_TIME)


def delete_proxy(isown, ip, site, logger=None):
    while True:
        try:
            url = '%s/delete?isown=%s&ip=%s&site=%s&token=%s' % (host, isown, ip, site, token)
            print(url)
            res = requests.get(url)
            return json.loads(res.text)['data']
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print(str(e))
            time.sleep(FAIL_SLEEP_TIME)


if __name__ == "__main__":
    print(get_proxy(isown=0, protocol=1, site='angel', count=1))
    # print delete_proxy(isown=0, ip='107.151.252.250', site='angel')

# coding:utf8
import json
import time

import requests

FAIL_SLEEP_TIME = 10
host = 'http://127.0.0.1:5003'
token = '4cc5fbe69e2a93d48bef68319b763541'


def get_proxy(count=1, logger=None):
    while True:
        try:
            url = '%s/select?token=%s&count=%s' % (
                host, token, count)
            print(url)
            res = requests.get(url)
            return json.loads(res.text)['data']
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print(str(e))
            time.sleep(FAIL_SLEEP_TIME)


def delete_proxy(ip, logger=None):
    while True:
        try:
            url = '%s/delete?isown=%s&ip=%s&site=%s&token=%s' % (host, ip, token)
            print(url)
            res = requests.get(url)
            return json.loads(res.text)['data']
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print
                str(e)
            time.sleep(FAIL_SLEEP_TIME)


if __name__ == "__main__":
    print(get_proxy( count=1))
    print(delete_proxy(ip='107.151.252.250'))

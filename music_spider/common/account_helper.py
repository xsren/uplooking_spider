# coding:utf8
import requests
import time
import json

FAIL_SLEEP_TIME = 10
host = 'http://127.0.0.1:5002'


def get_account(site, logger=None):
    while True:
        try:
            url = '%s/select?site=%s' % (host, site)
            res = requests.get(url)
            return json.loads(res.text)['data']
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print str(e)
            time.sleep(FAIL_SLEEP_TIME)


def delete_account(uid, logger=None):
    while True:
        try:
            url = '%s/delete?uid=%s' % (host, uid)
            res = requests.get(url)
            return json.loads(res.text)['data']
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print str(e)
            time.sleep(FAIL_SLEEP_TIME)


def insert_account(site, uname, passwd, cookie, email=None, logger=None):
    while True:
        try:
            url = '%s/insert?site=%s&uname=%s&passwd=%s&cookie=%s&email=%s' % (host, site, uname, passwd, cookie, email)
            res = requests.get(url)
            return json.loads(res.text)['data']
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print str(e)
            time.sleep(FAIL_SLEEP_TIME)

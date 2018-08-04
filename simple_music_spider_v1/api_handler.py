# coding:utf8
import json
import time
import traceback

import requests

HOST = 'http://127.0.0.1:5000'


def insert_task(task, logger):
    while True:
        try:
            url = '{}/insert_task?data={}'.format(HOST, json.dumps(task))
            res = requests.get(url)
            if res.status_code != 200:
                raise Exception('status_code:{}'.format(res.status_code))
            break
        except Exception as e:
            trace = traceback.format_exc()
            info = 'error:{},trace:{}'.format(str(e), trace)
            logger.error(info)
            time.sleep(5)

def run():
    pass


if __name__ == '__main__':
    run()

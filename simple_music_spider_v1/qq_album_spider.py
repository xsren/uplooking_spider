# coding:utf8
import json
import logging
import re
import time

import requests
from api_handler import get_task, insert_task, update_task
from mongo_handler import get_db

db = get_db()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
file_handler = logging.FileHandler("qq_song.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def crawl_album(t):
    try:
        # get album info
        # t['url'] = 'https://y.qq.com/n/yqq/album/003dGxVA1oaYac.html'

        alblum = {}
        alblum['album_Name'] = t['name']  # 专辑
        alblum['url'] = t['url']
        alblum['mid'] = t['mid']

        headers = {
            'authority': 'y.qq.com',
            'method': 'GET',
            'path': '/n/yqq/album/%s.html' % t['mid'],
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, sdch, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
        }
        _url_1 = t['url']
        res_1 = requests.get(_url_1, headers=headers).text
        if u"没有找到相关内容" in res_1:
            raise Exception('404 error ...')

        if re.search(r'类型：.*<', res_1):
            at = re.search(r'类型：.*<', res_1).group().replace(u'类型：', '').replace('<', '')
            alblum['album_Type'] = at  # 类别

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'c.y.qq.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
        }
        _url_2 = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_album_info_cp.fcg?albummid=%s&g_tk=5381&&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % \
                 t['mid']

        res_2 = requests.get(_url_2, headers=headers).text

        rj = json.loads(res_2)
        data = rj['data']

        if data['list'] is not None:
            for _l in data['list']:
                song_task = {
                    'last_crawl_time': 0,
                    'status': 0,
                    'mid': _l['songmid'],
                    'url': 'https://y.qq.com/n/yqq/song/%s.html' % _l['songmid'],
                    'name': _l['songname'],
                }
                insert_task('song_task', song_task, logger)



    except Exception as e:
        info = 'url:%s, error:%s' % (t['url'], str(e))
        print(info)


def run():
    while True:
        task = get_task('album_task', logger)
        print(task)

        t0 = time.time()
        crawl_album(task)
        update_task('album_task', task, 2, logger)
        info = "finish crawl url:%s, t_diff:%s" % (task['url'], time.time() - t0)
        print(info)


if __name__ == '__main__':
    run()

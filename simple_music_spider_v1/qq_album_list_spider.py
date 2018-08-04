# coding:utf8
import json
import logging
import random
import time

import requests
from api_handler import insert_task
from mongo_handler import get_db

db = get_db()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
file_handler = logging.FileHandler("qq_song.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def crawl_album_list(page, area):
    """抓取专辑列表页"""
    has_next_page = True
    callback = 'getUCGI{}'.format(str(random.random()).replace('0.', ''))
    param = 'callback={}&g_tk=5381&jsonpCallback={}&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&data=%7B%22albumlib%22%3A%7B%22method%22%3A%22get_album_by_tags%22%2C%22param%22%3A%7B%22area%22%3A{}%2C%22company%22%3A-1%2C%22genre%22%3A-1%2C%22type%22%3A-1%2C%22year%22%3A-1%2C%22sort%22%3A2%2C%22get_tags%22%3A1%2C%22sin%22%3A{}%2C%22num%22%3A20%2C%22click_albumid%22%3A0%7D%2C%22module%22%3A%22music.web_album_library%22%7D%7D'.format(
        callback, callback, area, page * 20)
    path = '/cgi-bin/musicu.fcg?{}'.format(param)
    headers = {
        'authority': 'u.y.qq.com',
        'method': 'GET',
        'path': path,
        'scheme': 'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,en-US;q=0.8,en;q=0.6,zh-CN;q=0.4,zh-TW;q=0.2',
        'referer': 'https://y.qq.com/portal/album_lib.html',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
    }
    url = "https://u.y.qq.com{}".format(path)
    res = requests.get(url, headers=headers, timeout=10)
    time.sleep(3)

    rj = json.loads(res.text.replace(callback, '').replace('(', '').replace(')', ''))
    album_list = rj['albumlib']['data']['list']
    if len(album_list) == 0:
        print(' len(album_list) == 0 ...')
        has_next_page = False
        return has_next_page
    album_tasks = []
    for album in album_list:
        album_task = {
            'last_crawl_time': 0,
            'status': 0,
            'mid': album['album_mid'],
            'url': 'https://y.qq.com/n/yqq/album/%s.html' % album['album_mid'],
            'name': album['album_name'],
        }
        album_tasks.append(album_task)
        insert_task(album_task, logger)
        # if not db['album_task'].find_one({'url': album_task['url']}):
        #     db['album_task'].insert_one(album_task)
    return has_next_page


def run():
    """根据列表页抓取最新的专辑，可以以此来实现增量抓取歌曲"""

    areas = [1, 0, 3, 15, 14, 4]
    logger.info('start...')
    for area in areas:
        page = 0
        while page <= 3:
            print('page: %s ......' % page)
            try:
                has_next_page = crawl_album_list(page, area)
                if not has_next_page:
                    break
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(str(e))
            page += 1
    print('finish .....')


if __name__ == '__main__':
    run()

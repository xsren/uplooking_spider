# coding:utf8
import json
import logging
import threading
import time

import requests
from mongo_handler import get_db

db = get_db()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S', )
file_handler = logging.FileHandler("qq_song.log")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def crawl_song(t, t_num):
    try_times = 3
    while try_times > 0:
        try_times -= 1
        try:
            # get song info

            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Connection': 'keep-alive',
                'Host': 'c.y.qq.com',
                'Referer': t['url'],
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            }

            _url_1 = 'https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg?songmid=%s&tpl=yqq_song_detail&format=jsonp&g_tk=5381&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % \
                     t['mid']
            res_1 = requests.get(_url_1, headers=headers).text

            rj_1 = json.loads(res_1[1:-1])
            if rj_1['code'] == 400:
                logger.warning('invalid task:%s' % t['url'])
                db['song_task'].update_one({'url': t['url']}, {'$set': {'status': 4}})
                return
            data = rj_1['data'][0]

            song = {}
            song['is_to_mysql'] = 0
            song['mus_Name'] = t['name']  # 歌曲
            song['url'] = t['url']
            try:
                song['mid'] = data['file']['media_mid']
            except:
                song['mid'] = t['mid']
            song['mus_Singer'] = [{'name': s['name'], 'mid': s['mid']} for s in data['singer']]  # 歌手 是列表

            song['mus_Album'] = data['album']['name']  # 专辑
            song['album_mid'] = data['album']['mid']
            song['album_url'] = 'https://y.qq.com/n/yqq/album/%s.html' % data['album']['mid']
            song['mus_Time'] = data['interval']  # 时长

            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Connection': 'keep-alive',
                'Host': 'c.y.qq.com',
                'Referer': t['url'],
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            }
            _url_2 = 'https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric.fcg?nobase64=1&musicid=%s&g_tk=5381&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % \
                     data['id']

            res_2 = requests.get(_url_2, headers=headers).text

            rj = json.loads(res_2.replace('MusicJsonCallback(', '').replace(')', ''))
            if 'lyric' in rj:
                song['mus_Lyric'] = rj['lyric']  # 歌词
            else:
                song['mus_Lyric'] = ''

            if not db['song_info'].find_one({'url': song['url']}):
                db['song_info'].insert_one(song)
            db['song_task'].update_one({'url': t['url']}, {'$set': {'status': 2}})
            return
        except Exception as e:
            info = 't_num:%s,url:%s, error:%s' % (t['url'], str(e), t_num)
            logger.info(info)
            logger.exception(e)
            time.sleep(1)

    db['song_task'].update_one({'url': t['url']}, {'$set': {'status': 3}})


def run_spider(t_num):
    while True:
        try:
            task = db['song_task'].find_and_modify({'status': 0}, {'$set': {'status': 1}})

            if not task:
                logger.info('t_num:{},finish crawl all task'.format(t_num))
                return

            t0 = time.time()
            crawl_song(task, t_num)
            info = "t_num:%s, finish crawl url:%s, t_diff:%s" % (t_num, task['url'], time.time() - t0)
            logger.info(info)
        except Exception as e:
            logger.exception(e)
            time.sleep(3)


def run():
    threads = []
    thread_num = 10
    for i in range(thread_num):
        t1 = threading.Thread(target=run_spider, args=(i,))
        threads.append(t1)

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    run()

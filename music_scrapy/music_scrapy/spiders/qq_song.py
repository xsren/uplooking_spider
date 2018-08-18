# -*- coding: utf-8 -*-
import json

import scrapy
from music_scrapy.common.mongo_handler import get_db


def gen_headers(mid, url):
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'c.y.qq.com',
        'Referer': url,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
    }
    url = 'https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg?songmid=%s&tpl=yqq_song_detail&format=jsonp&g_tk=5381&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % mid
    return url, headers


class QqSongSpider(scrapy.Spider):
    name = "qq_song"

    # allowed_domains = ["y.qq.com"]
    # start_urls = ['http://y.qq.com/']

    def __init__(self):
        self.db = get_db()

    def _get_task(self):
        task = self.db['song_task'].find_and_modify({'status': 0}, {'$set': {'status': 1}})
        if not task:
            return
        mid = task['mid']
        m_url = task['url']
        name = task['name']
        url, headers = gen_headers(mid, m_url)
        meta = {
            'm_url': m_url,
            'name': name,
            'mid': mid,
        }
        return scrapy.Request(url=url, headers=headers, callback=self.parse, meta=meta)

    def start_requests(self):

        task = self._get_task()
        if not task:
            print('no task to crawl')
            return
        yield task

    def parse(self, response):
        # 解析数据
        # print(response.text)
        rj_1 = json.loads(response.text[1:-1])

        code = rj_1['code']
        m_url = response.meta['m_url']
        name = response.meta['name']
        mid = response.meta['mid']

        if code == 400:
            print('invalid task:%s' % m_url)
            self.db['song_task'].update_one({'url': m_url}, {'$set': {'status': 4}})
            return
        data = rj_1['data'][0]

        song = {}
        song['is_to_mysql'] = 0
        song['mus_Name'] = name  # 歌曲
        song['url'] = m_url
        try:
            song['mid'] = data['file']['media_mid']
        except:
            song['mid'] = mid
        song['mus_Singer'] = [{'name': s['name'], 'mid': s['mid']} for s in data['singer']]  # 歌手 是列表

        song['mus_Album'] = data['album']['name']  # 专辑
        song['album_mid'] = data['album']['mid']
        song['album_url'] = 'https://y.qq.com/n/yqq/album/%s.html' % data['album']['mid']
        song['mus_Time'] = data['interval']  # 时长

        res = {
            'data': song,
            'coll_name': 'song_info',
        }

        yield res

        # 更新任务
        self.db['song_task'].update_one({'url': m_url}, {'$set': {'status': 2}})

        # 爬取下一个
        task = self._get_task()
        if not task:
            print('no task to crawl')
            return
        yield task

# -*- coding: utf-8 -*-
import json

import scrapy
from music_scrapy.common.mongo_handler import get_db


def gen_headers(mid):
    headers = {
        'authority': 'y.qq.com',
        'method': 'GET',
        'path': '/n/yqq/album/%s.html' % mid,
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, sdch, br',
        'accept-language': 'zh-CN,zh;q=0.8',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
    }
    url = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_album_info_cp.fcg?albummid=%s&g_tk=5381&&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % mid
    return url, headers


class QqAlbumSpider(scrapy.Spider):
    name = "qq_album"

    # allowed_domains = ["y.qq.com"]
    # start_urls = ['http://y.qq.com/']
    def __init__(self):
        self.db = get_db()

    def _get_task(self):
        task = self.db['album_task'].find_and_modify({'status': 0}, {'$set': {'status': 1}})
        if not task:
            return
        mid = task['mid']
        m_url = task['url']
        url, headers = gen_headers(mid)
        meta = {'m_url': m_url}
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
        rj = json.loads(response.text)

        code = rj['code']
        m_url = response.meta['m_url']
        if code != 0:
            self.db['album_task'].update_one({'url': m_url}, {'$set': {'status': 3}})

        else:
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

                    res = {
                        'data': song_task,
                        'coll_name': 'song_task',
                    }

                    yield res

            # 更新任务
            self.db['album_task'].update_one({'url': m_url}, {'$set': {'status': 2}})

        # 爬取下一个
        task = self._get_task()
        if not task:
            print('no task to crawl')
            import pdb
            pdb.set_trace()
            return
        yield task

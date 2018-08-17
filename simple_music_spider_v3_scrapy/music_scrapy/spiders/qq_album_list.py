# -*- coding: utf-8 -*-
import json
import random

import scrapy


def generate_url_and_headers(area, page):
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
    return url, headers, callback


class QqAlbumListSpider(scrapy.Spider):
    name = "qq_album_list"
    # allowed_domains = ["y.qq.com"]
    # start_urls = ['http://y.qq.com/']
    page_limit = 3

    def start_requests(self):
        areas = [1, 0, 3, 15, 14, 4]
        areas = [1]
        page = 0
        for area in areas:
            url, headers, _cb = generate_url_and_headers(area, page)
            meta = {'area': area,
                    'page': page,
                    'callback': _cb}
            yield scrapy.Request(url=url, headers=headers, meta=meta, callback=self.parse)

    def parse(self, response):
        meta = response.meta
        page = meta['page']
        area = meta['area']
        _cb = meta['callback']
        rj = json.loads(response.text.replace(_cb, '').replace('(', '').replace(')', ''))
        album_list = rj['albumlib']['data']['list']
        if len(album_list) == 0:
            print(' len(album_list) == 0 ...')
            return
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

            yield album_task

        if page < self.page_limit:
            new_page = page + 1
            url, headers, _cb = generate_url_and_headers(area, new_page)
            meta = {'area': area,
                    'page': new_page,
                    'callback': _cb}
            yield scrapy.Request(url=url, headers=headers, meta=meta, callback=self.parse)

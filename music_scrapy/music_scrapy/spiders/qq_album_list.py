# -*- coding: utf-8 -*-
import json
import random

import scrapy


def gen_url_and_headers(area, page):
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
    page_limit = 20000

    # allowed_domains = ["y.qq.com"]
    # start_urls = ['http://y.qq.com/']
    
    def gen_request(self, area, page, spec_page_limit, try_times):
        url, headers, callback = gen_url_and_headers(area, page)
        meta = {
            'page': page,
            'area': area,
            'callback': callback,
            'spec_page_limit': spec_page_limit,
            'try_times': try_times,
        }
        return scrapy.Request(url=url, headers=headers, callback=self.parse_a, meta=meta)

    def start_requests(self):
        areas = [(1, 3260), (0, 607), (3, 20918), (15, 2363), (14, 540), (4, 232)]
        # areas = [1]
        page = 0
        for area, spec_page_limit in areas:
            yield self.gen_request(area, page, spec_page_limit, try_times=0)

    def parse_a(self, response):
        area = response.meta['area']
        callback = response.meta['callback']
        spec_page_limit = response.meta['spec_page_limit']
        try_times = response.meta['try_times']
        # res = {
        #     'data': response.text,
        #     'area': area,
        #     'page': response.meta['page'],
        # }
        # yield res

        # 解析数据
        rj = json.loads(response.text.replace(callback, '').replace('(', '').replace(')', ''))
        album_list = rj['albumlib']['data']['list']
        # 判断是否是最后一页
        if len(album_list) == 0:
            if try_times < 5:
                page = response.meta['page']
                # url, headers, callback = gen_url_and_headers(area, page)
                # meta = {
                #     'page': page,
                #     'area': area,
                #     'callback': callback,
                #     'spec_page_limit': spec_page_limit,
                #     'try_times': try_times + 1,
                # }
                # yield scrapy.Request(url=url, headers=headers, callback=self.parse_a, meta=meta)
                yield self.gen_request(area, page, spec_page_limit, try_times=try_times + 1)
            else:
                print(' len(album_list) == 0 ...')
                return
        for album in album_list:
            album_task = {
                'last_crawl_time': 0,
                'status': 0,
                'mid': album['album_mid'],
                'url': 'https://y.qq.com/n/yqq/album/%s.html' % album['album_mid'],
                'name': album['album_name'],
            }

            res = {
                'data': album_task,
                'coll_name': 'album_task',
            }

            yield res

        page = response.meta['page'] + 1
        if page < self.page_limit and page <= spec_page_limit:
            # 翻页
            yield self.gen_request(area, page, spec_page_limit, try_times=0)
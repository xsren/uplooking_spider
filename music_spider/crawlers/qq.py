# coding:utf8

'''
angel
https://angel.co
口碑暂时不做
'''

import copy
import json
import re
import string
# 系统库
import sys
import time
import traceback
from xml.etree.ElementTree import fromstring

from xmljson import badgerfish as bf

# 本地库
sys.path.append('../common')
sys.path.append('../main')
from BaseCrawler import BaseCrawler
import common
import random

siteHost = "https://y.qq.com"
site_source = 'qq'


class Crawler(BaseCrawler):
    def __init__(self, threadID, logger, ttype, proxy_type, sock, seeds, register, login):
        import pdb
        pdb.set_trace()
        BaseCrawler.__init__(self, threadID, logger, ttype, site_source, siteHost, proxy_type, sock, seeds, limit=10,
                             timeout=15)
        self.dbName = "songs"
        self.count = 0
        self.register_flag = register
        self.login_flag = login

    def crawl_album_list(self):
        """根据列表页抓取最新的专辑，可以以此来实现增量抓取歌曲"""

        areas = [1, 0, 3, 15, 14, 4]
        self.logger.info('start .....')
        for area in areas:
            page = 0
            while page <= 30:
                self.logger.info('page: %s ......' % page)
                try:
                    has_next_page = self.__crawl_album_list(page, area)
                    if not has_next_page:
                        break
                except Exception as e:
                    self.logger.warning(str(e))
                page += 1
        self.logger.info('finish .....')

    def __crawl_album_list(self, page, area):
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
        res = self.openUrl(url, headers=headers, timeout=10)
        time.sleep(3)
        if res is None:
            raise Exception("res is None...... change proxy ......")
        rj = json.loads(res.replace(callback, '').replace('(', '').replace(')', ''))
        album_list = rj['albumlib']['data']['list']
        if len(album_list) == 0:
            self.logger.info(' len(album_list) == 0 ...')
            has_next_page = False
            return has_next_page
        album_tasks, singer_tasks = [], []
        for album in album_list:
            album_task = {
                'last_crawl_time': 0,
                'status': 0,
                'mid': album['album_mid'],
                'url': 'https://y.qq.com/n/yqq/album/%s.html' % album['album_mid'],
                'name': album['album_name'],
            }
            album_tasks.append(album_task)
            for singer in album['singers']:
                singer_task = {
                    'last_crawl_time': 0,
                    'status': 0,
                    'mid': singer['singer_mid'],
                    'url': 'https://y.qq.com/n/yqq/singer/%s.html' % singer['singer_mid'],
                    'name': singer['singer_name'],
                }
                singer_tasks.append(singer_task)

        if len(singer_tasks) > 0:
            self.sock.put_task(self.dbName, "%s_singer_tasks" % self.siteName, singer_tasks)
        if len(album_tasks) > 0:
            self.sock.put_task(self.dbName, "%s_album_tasks" % self.siteName, album_tasks)
        return has_next_page

    def crawl_playlist_index(self):
        """之前是抓取指定的几个分类，现在是抓取所有的"""
        types = [
            ('new_playlist', 4),
            ('recommend_playlist', 4),
        ]
        for t in types:
            t0 = time.time()
            self.__crawl_playlist_index(t[0], t[1])
            info = "finish crawl t_diff:%s" % (time.time() - t0)
            self.logger.info(info)

    def __crawl_playlist_index(self, playlist_type, max_page):
        """从第一页开始往下翻页"""
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'c.y.qq.com',
            'Referer': 'https://y.qq.com/portal/playlist.html',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
        }

        if playlist_type == 'new_playlist':
            sort_id = 2
        elif playlist_type == 'recommend_playlist':
            sort_id = 5
        else:
            raise Exception(u'未知的 playlist_type:{}'.format(playlist_type))
        pagenum = 0
        while pagenum < max_page:
            self.logger.info('begin to crawl page {}, type {}'.format(pagenum, playlist_type))

            _url = 'https://c.y.qq.com/splcloud/fcgi-bin/fcg_get_diss_by_tag.fcg?picmid=1&rnd={}&g_tk=5381&jsonpCallback=getPlaylist&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&categoryId=10000000&sortId={}&sin={}&ein={}'.format(
                random.random(), sort_id, pagenum * 30, (pagenum + 1) * 30 - 1)
            try:
                res = self.openUrl(_url, headers=headers)
                time.sleep(1)
                if res is None:
                    raise Exception("res is None...... change proxy ......")
                rj = json.loads(res.replace('getPlaylist(', '').replace(')', ''))
                _list = rj['data']['list']
                ts = []
                ranks = []
                index = pagenum * 30
                for _l in _list:
                    # 排行榜相关
                    rank = {
                        'url': index,
                        'dissid': _l['dissid'],
                        'name': _l['dissname'],
                    }
                    ranks.append(rank)
                    # 歌单task
                    _t = {
                        'dissid': _l['dissid'],
                        'name': _l['dissname'],
                        'url': 'https://y.qq.com/n/yqq/playlist/%s.html' % _l['dissid'],
                        'status': 0,
                        'last_crawl_time': 0,
                    }
                    ts.append(_t)
                    index += 1
                self.logger.info('get new task num:%s' % len(ts))
                if len(ranks):
                    self.sock.insert_data(self.dbName, playlist_type, ranks)

                if len(ts) > 0:
                    self.sock.put_task(self.dbName, "%s_playlist_tasks" % self.siteName, ts)
                if len(ts) < 30:
                    break
                self.logger.info('finish to crawl page {}, type {}'.format(pagenum, playlist_type))
                pagenum += 1
            except Exception as e:
                self.logger.warning(str(e))
                self.init_session()

    def crawl_playlist(self):
        while True:
            ts = self.sock.get_task(self.dbName, "%s_playlist_tasks" % self.siteName)['data']
            if len(ts) == 0:
                self.logger.warning('no task to crawl ......')
                return
            for t in ts:
                t0 = time.time()
                self.__crawl_playlist(t)
                info = "finish crawl url:%s, t_diff:%s" % (t['url'], time.time() - t0)
                self.logger.info(info)
                self.count += 1

    def __crawl_playlist(self, t):

        try:
            # get singer info
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Connection': 'keep-alive',
                'Host': 'c.y.qq.com',
                'Referer': t['url'],
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            }
            _url_1 = 'https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg?type=1&json=1&utf8=1&onlysong=0&disstid=%s&format=jsonp&g_tk=5381&jsonpCallback=playlistinfoCallback&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % \
                     t['dissid']

            res_1 = self.openUrl(_url_1, headers=headers)

            rj = json.loads(res_1.replace('playlistinfoCallback(', '').replace(')', ''))
            data = rj['cdlist'][0]

            playlist = {}
            playlist['is_to_mysql'] = 0
            playlist['url'] = t['url']
            playlist['dissid'] = t['dissid']
            playlist['playlist_Name'] = data['dissname']  # 歌单名
            playlist['playlist_Editor'] = data['nick']  # 创建人
            playlist['playlist_Summary'] = data['desc']  # 简介
            playlist['playlist_Cover'] = data['logo']  # 封面
            playlist['playlist_Tag'] = [tag['name'] for tag in data['tags']]  # 标签

            ml = []
            song_tasks = []
            for s in data['songlist']:
                if 'strMediaMid' not in s:
                    continue
                m = {
                    'url': 'https://y.qq.com/n/yqq/song/%s.html' % s['strMediaMid'],
                    'name': s['songname'],
                    'mid': s['strMediaMid'],
                }
                ml.append(m)
                song_task = {
                    "status": 0,
                    "last_crawl_time": 0,
                    "name": s['songname'],
                    "url": "https://y.qq.com/n/yqq/song/%s.html" % s['strMediaMid'],
                    "mid": s['strMediaMid']
                }
                song_tasks.append(song_task)

            playlist['playlist_Mus_List'] = ml  # 歌曲

            # put song tasks
            if len(song_tasks) > 0:
                self.sock.put_task(self.dbName, "%s_song_tasks" % self.siteName, song_tasks)
            # put playlist
            self.sock.insert_data(self.dbName, "%s_playlist" % self.siteName, [playlist])
            self.sock.change_task_status(self.dbName, "%s_playlist_tasks" % self.siteName,
                                         [{'url': t['url'], 'status': common.CRAWL_SUCCESS}])

        except Exception as e:
            info = 'url:%s, error:%s' % (t['url'], str(e))
            self.logger.warning(info)
            # utils.send_email(info,attach=res)
            self.sock.change_task_status(self.dbName, "%s_playlist_tasks" % self.siteName,
                                         [{'url': t['url'], 'status': common.CRAWL_FAIL}])
            self.init_session()

    def init_singer_tasks(self):
        tag_list = [('cn_man', u'华语男'),
                    ('cn_woman', u'华语女'),
                    ('cn_team', u'华语组合'),
                    ('k_man', u'韩国男'),
                    ('k_woman', u'韩国女'),
                    ('k_team', u'韩国组合'),
                    ('j_man', u'日本男'),
                    ('j_woman', u'日本女'),
                    ('j_team', u'日本组合'),
                    ('eu_man', u'欧美男'),
                    ('eu_woman', u'欧美女'),
                    ('eu_team', u'欧美组合'),
                    ('c_orchestra', u'乐团'),
                    ('c_performer', u'演奏家'),
                    ('c_composer', u'作曲家'),
                    ('c_cantor', u'指挥家'),
                    ('other_other', u'其他'),

                    ]
        letter_list = list(string.uppercase) + ['9']

        ts = []
        for tag in tag_list:
            for letter in letter_list:
                t = {'url': '%s_%s' % (tag[0], letter),
                     'tag': tag[1],
                     'tag_en': tag[0],
                     'status': 0,
                     'last_crawl_time': 0,
                     'index': self.format_index(letter),
                     }
                ts.append(t)
        if len(ts) > 0:
            self.sock.put_task(self.dbName, "%s_singer_index_tasks" % self.siteName, ts)

    def format_index(self, letter):
        if letter == '9':
            return '#'
        else:
            return letter

    def crawl_singer_index(self):
        while True:
            ts = self.sock.get_task(self.dbName, "%s_singer_index_tasks" % self.siteName)['data']
            if len(ts) == 0:
                self.logger.warning('no task to crawl ......')
                return
            for t in ts:
                t0 = time.time()
                self.__crawl_singer_index(t)
                info = "finish crawl url:%s, t_diff:%s" % (t['url'], time.time() - t0)
                self.logger.info(info)
                self.count += 1

    def __crawl_singer_index(self, t):

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'zh,en-US;q=0.8,en;q=0.6,zh-CN;q=0.4,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'Host': 'c.y.qq.com',
            'Referer': 'https://y.qq.com/portal/singer_list.html',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
        }

        pagenum = 1

        while True:
            _url = 'https://c.y.qq.com/v8/fcg-bin/v8.fcg?channel=singer&page=list&key=%s&pagesize=100&pagenum=%s&g_tk=5381&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % (
                t['url'], pagenum)

            try:
                res = self.openUrl(_url, headers=headers)
                if res is None:
                    raise Exception('res is None...... change proxy......')
                # 最后一页为空
                if len(res) < 10:
                    break
                rj = json.loads(res)
                _list = rj['data']['list']
                ts = []
                for _l in _list:
                    _t = copy.deepcopy(t)
                    mid = _l['Fsinger_mid']
                    _t['url'] = 'https://y.qq.com/n/yqq/singer/%s.html' % mid
                    _t['mid'] = mid
                    _t['name'] = _l['Fsinger_name']
                    ts.append(_t)

                self.logger.info('get new task num:%s' % len(ts))

                if len(ts) > 0:
                    self.sock.put_task(self.dbName, "%s_singer_tasks" % self.siteName, ts)
                pagenum += 1
            except Exception as e:
                self.logger.warning(str(e))
                self.init_session()

        self.sock.change_task_status(self.dbName, "%s_singer_index_tasks" % self.siteName,
                                     [{'url': t['url'], 'status': common.CRAWL_SUCCESS}])

    def crawl_singer(self):
        while True:
            ts = self.sock.get_task(self.dbName, "%s_singer_tasks" % self.siteName)['data']
            if len(ts) == 0:
                self.logger.warning('no task to crawl ......')
                return
            for t in ts:
                t0 = time.time()
                self.__crawl_singer(t)
                info = "finish crawl url:%s, t_diff:%s" % (t['url'], time.time() - t0)
                self.logger.info(info)
                self.count += 1

    def __crawl_singer(self, t):

        try:
            # get singer info
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Connection': 'keep-alive',
                'Host': 'c.y.qq.com',
                'Referer': 'https://c.y.qq.com/xhr_proxy_utf8.html',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            }
            _url_1 = 'https://c.y.qq.com/splcloud/fcgi-bin/fcg_get_singer_desc.fcg?singermid=%s&utf8=1&outCharset=utf-8&format=xml&r=%s' % (
                t['mid'], int(time.time() * 1000))

            res_1 = self.openUrl(_url_1, headers=headers)

            rj = json.loads(json.dumps(bf.data(fromstring(res_1.encode('utf-8')))))
            data = rj['result']['data']
            singer = {}
            singer['url'] = t['url']
            singer['mid'] = t['mid']
            singer['singr_Name'] = t['name']  # 歌手
            singer['singr_Type'] = t.get('tag', '')  # 类别 华语男艺人、华语组合…
            singer['singr_Img'] = 'https://y.gtimg.cn/music/photo_new/T001R300x300M000%s.jpg' % t['mid']  # 艺人图片
            if 'tag_en' in t:
                if 'man' in t['tag_en']:
                    singer['singr_Gender'] = 'man'
                elif 'woman' in t['tag_en']:
                    singer['singr_Gender'] = 'woman'

                if 'cn_' in t['tag_en']:
                    singer['singr_Station'] = u'中国'  # 地区
                elif 'k_' in t['tag_en']:
                    singer['singr_Station'] = u'韩国'  # 地区
                elif 'j_' in t['tag_en']:
                    singer['singr_Station'] = u'日本'  # 地区
                elif 'eu_' in t['tag_en']:
                    singer['singr_Station'] = u'欧美'  # 地区
            else:
                singer['singr_Gender'] = ''
                singer['singr_Station'] = ''
            # 有的可能没有歌手信息
            if 'info' in data:
                info = data['info']
                basic = info['basic']
                if "item" in basic:
                    items = basic['item']

                    # singer = {}
                    # singer['url'] = t['url']
                    # singer['mid'] = t['mid']
                    # singer['singr_Name'] = t['name'] # 歌手
                    # # 我加的
                    # singer['tag_en'] = t['tag_en']
                    # singer['singr_Img'] = 'https://y.gtimg.cn/music/photo_new/T001R300x300M000%s.jpg'%t['mid'] # 艺人图片
                    # singer['singr_Type'] = t['tag'] # 类别 华语男艺人、华语组合…
                    # singer['singr_Eng_name'] = t['name'] # 外文名
                    # singer['singr_Gender'] = t['name'] # 性别

                    # singer['singr_Birthday'] = t['name'] # 生日
                    # singer['singr_Nationality'] = t['name'] # 国籍
                    # singer['singr_Birthplace'] = t['name'] # 出生地
                    # singer['singr_Station'] = t['name'] # 地区
                    # singer['singr_Occupation'] = t['name'] # 职业

                    # singer['singr_Style'] = t['name'] # 风格 国语流行 Mandarin Pop, 粤语流行 Cantopop
                    # singer['singr_MainWorks'] = t['name'] # 代表作品
                    # singer['singr_Summary'] = info['desc']['$'] # 简介

                    try:
                        singer['singr_Summary'] = info['desc']['$']  # 简介
                    except:
                        singer['singr_Summary'] = ""

                    try:
                        for item in items:
                            k = item['key'].get('$', '')
                            v = item['value'].get('$', '')
                            if k == u'\u5916\u6587\u540d':
                                singer['singr_Eng_name'] = v  # 外文名
                            elif k == u'\u751f\u65e5':
                                singer['singr_Birthday'] = v  # 生日
                            elif k == u'\u56fd\u7c4d':
                                singer['singr_Nationality'] = v  # 国籍
                            elif k == u'\u51fa\u751f\u5730':
                                singer['singr_Birthplace'] = v  # 出生地
                            elif k == u'\u804c\u4e1a':
                                singer['singr_Occupation'] = v  # 职业
                            elif k == u'\u4ee3\u8868\u4f5c\u54c1':
                                singer['singr_MainWorks'] = v  # 代表作品
                    except:
                        pass

            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Host': 'c.y.qq.com',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            }

            begin = 0
            ats = []
            while True:
                _url_2 = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_singer_album.fcg?g_tk=5381&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&singermid=%s&order=time&begin=%s&num=30&exstatus=1' % (
                    t['mid'], begin)
                res_2 = self.openUrl(_url_2, headers=headers)
                rj = json.loads(res_2)
                total = rj['data']['total']
                if rj['data']['list'] is not None:
                    for _l in rj['data']['list']:
                        _t = {
                            'last_crawl_time': 0,
                            'status': 0,
                            'mid': _l['albumMID'],
                            'url': 'https://y.qq.com/n/yqq/album/%s.html' % _l['albumMID'],
                            'name': _l['albumName'],
                        }
                        ats.append(_t)

                if len(ats) >= total:
                    break
                begin += len(ats)

            # put singer
            self.sock.insert_data(self.dbName, "%s_singer" % self.siteName, [singer])
            # put alblum tasks
            if len(ats) > 0:
                self.sock.put_task(self.dbName, "%s_album_tasks" % self.siteName, ats)
            self.sock.change_task_status(self.dbName, "%s_singer_tasks" % self.siteName,
                                         [{'url': t['url'], 'status': common.CRAWL_SUCCESS}])

        except Exception as e:
            info = 'url:%s, error:%s' % (t['url'], str(e))
            self.logger.warning(info)
            # utils.send_email(info,attach=res)

            if "mismatched tag:" in str(e) or "not well-formed" in str(e) or "unclosed CDATA section" in str(
                    e) or "basic" in str(e) or "tag" in str(e):
                self.sock.change_task_status(self.dbName, "%s_singer_tasks" % self.siteName,
                                             [{'url': t['url'], 'status': common.INVALID_TASK}])
            else:
                self.sock.change_task_status(self.dbName, "%s_singer_tasks" % self.siteName,
                                             [{'url': t['url'], 'status': common.CRAWL_FAIL}])
            self.init_session()

            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch, br',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Host': 'c.y.qq.com',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
            }

            begin = 0
            ats = []
            while True:
                _url_2 = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_singer_album.fcg?g_tk=5381&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&singermid=%s&order=time&begin=%s&num=30&exstatus=1' % (
                    t['mid'], begin)
                res_2 = self.openUrl(_url_2, headers=headers)
                rj = json.loads(res_2)
                total = rj['data']['total']
                if rj['data']['list'] is not None:
                    for _l in rj['data']['list']:
                        _t = {
                            'last_crawl_time': 0,
                            'status': 0,
                            'mid': _l['albumMID'],
                            'url': 'https://y.qq.com/n/yqq/album/%s.html' % _l['albumMID'],
                            'name': _l['albumName'],
                            '': 0,

                        }
                        ats.append(_t)

                if len(ats) >= total:
                    break
                begin += len(ats)
            # put alblum tasks
            if len(ats) > 0:
                self.sock.put_task(self.dbName, "%s_album_tasks" % self.siteName, ats)

    def crawl_album(self):
        while True:
            ts = self.sock.get_task(self.dbName, "%s_album_tasks" % self.siteName)['data']
            if len(ts) == 0:
                self.logger.warning('no task to crawl ......')
                return
            for t in ts:
                t0 = time.time()
                self.__crawl_album(t)
                info = "finish crawl url:%s, t_diff:%s" % (t['url'], time.time() - t0)
                self.logger.info(info)
                self.count += 1

    def __crawl_album(self, t):
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
            res_1 = self.openUrl(_url_1, headers=headers)
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

            res_2 = self.openUrl(_url_2, headers=headers)

            rj = json.loads(res_2)
            data = rj['data']

            # alblum = {}
            # alblum['album_Name'] = # 专辑
            # alblum['album_Byname'] = # 外文名
            # alblum['album_Singr'] = # 歌手
            # alblum['album_Genre'] = # 流派
            # alblum['album_lan'] = # 语种
            # alblum['album_Pub_Time'] = # 发行时间
            # alblum['album_Company'] = # 发行公司
            # alblum['album_Type'] = # 类别
            # alblum['album_Cover'] = # 封面
            # alblum['album_Mus_List'] = # 歌曲列表
            # alblum['album_Summary'] = # 简介
            # alblum['album_Tag'] = # 标签

            alblum['sing_url'] = 'https://y.qq.com/n/yqq/singer/%s.html' % data['singermid']
            alblum['sing_mid'] = data['singermid']
            alblum['album_Singr'] = data['singername']  # 歌手
            alblum['album_Genre'] = data['genre']  # 流派
            alblum['album_lan'] = data['lan']  # 语种
            alblum['album_Pub_Time'] = data['aDate']  # 发行时间
            alblum['album_Company'] = data['company']  # 发行公司
            alblum['album_Cover'] = 'https://y.gtimg.cn/music/photo_new/T002R300x300M000%s.jpg' % t['mid']  # 封面
            alblum['album_Summary'] = data['desc']  # 简介

            sts = []
            if data['list'] is not None:
                for _l in data['list']:
                    _t = {
                        'last_crawl_time': 0,
                        'status': 0,
                        'mid': _l['songmid'],
                        'url': 'https://y.qq.com/n/yqq/song/%s.html' % _l['songmid'],
                        'name': _l['songname'],
                    }
                    sts.append(_t)

                    # put album
            self.sock.insert_data(self.dbName, "%s_album" % self.siteName, [alblum])
            # put song tasks
            if len(sts) > 0:
                self.sock.put_task(self.dbName, "%s_song_tasks" % self.siteName, sts)
            self.sock.change_task_status(self.dbName, "%s_album_tasks" % self.siteName,
                                         [{'url': t['url'], 'status': common.CRAWL_SUCCESS}])


        except Exception as e:
            info = 'url:%s, error:%s' % (t['url'], str(e))
            self.logger.warning(info)
            # utils.send_email(info,attach=res)
            if '404 error' in str(e):
                self.sock.change_task_status(self.dbName, "%s_album_tasks" % self.siteName,
                                             [{'url': t['url'], 'status': common.INVALID_TASK}])
            else:
                self.sock.change_task_status(self.dbName, "%s_album_tasks" % self.siteName,
                                             [{'url': t['url'], 'status': common.CRAWL_FAIL}])
            self.init_session()

    def crawl_song(self):
        while True:
            ts = self.sock.get_task(self.dbName, "%s_song_tasks" % self.siteName)['data']
            if len(ts) == 0:
                self.logger.warning('no task to crawl ......')
                return
            for t in ts:
                t0 = time.time()
                self.__crawl_song(t)
                info = "finish crawl url:%s, t_diff:%s" % (t['url'], time.time() - t0)
                self.logger.info(info)
                self.count += 1

    def __crawl_song(self, t):
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
            res_1 = self.openUrl(_url_1, headers=headers)

            rj_1 = json.loads(res_1[1:-1])
            if rj_1['code'] == 400:
                self.logger.warning('invalid task:%s' % t['url'])
                self.sock.change_task_status(self.dbName, "%s_song_tasks" % self.siteName,
                                             [{'url': t['url'], 'status': common.INVALID_TASK}])
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

            # if data['pay']['price_album'] == 0:
            #     song['isFree'] = 0  # 免费
            # else:
            #     song['isFree'] = 1  # 付费

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

            res_2 = self.openUrl(_url_2, headers=headers)

            rj = json.loads(res_2.replace('MusicJsonCallback(', '').replace(')', ''))
            if 'lyric' in rj:
                song['mus_Lyric'] = rj['lyric']  # 歌词
            else:
                song['mus_Lyric'] = ''

            # put song
            self.sock.insert_data(self.dbName, "%s_song" % self.siteName, [song])
            self.sock.change_task_status(self.dbName, "%s_song_tasks" % self.siteName,
                                         [{'url': t['url'], 'status': common.CRAWL_SUCCESS}])


        except Exception as e:
            info = 'url:%s, error:%s' % (t['url'], str(e))
            self.logger.warning(info)
            # utils.send_email(info,attach=res)
            self.sock.change_task_status(self.dbName, "%s_song_tasks" % self.siteName,
                                         [{'url': t['url'], 'status': common.CRAWL_FAIL}])
            self.init_session()

    def crawl_rank_songs(self):
        self.crawl_hot_songs()
        self.crawl_new_songs()

    def crawl_hot_songs(self):
        """热歌榜单"""
        import pdb
        pdb.set_trace()
        for page in range(4):
            self.__crawl_rank_songs("hot_songs", page)

    def crawl_new_songs(self):
        """新歌榜单"""
        for page in range(4):
            self.__crawl_rank_songs("new_songs", page)

    def __crawl_rank_songs(self, rank_type, page, song_num=30):
        import pdb
        pdb.set_trace()
        self.logger.info("begin to crawl {} , page:{}".format(rank_type, page))
        if rank_type == "hot_songs":
            path = '/v8/fcg-bin/fcg_v8_toplist_cp.fcg?tpl=3&page=detail&topid=4&type=top&song_begin={}&song_num={}&g_tk=5381&jsonpCallback=MusicJsonCallbacktoplist&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0'.format(
                page * song_num, song_num)
        elif rank_type == "new_songs":
            path = '/v8/fcg-bin/fcg_v8_toplist_cp.fcg?tpl=3&page=detail&topid=27&type=top&song_begin={}&song_num={}&g_tk=5381&jsonpCallback=MusicJsonCallbacktoplist&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0'.format(
                page * song_num, song_num)
        else:
            raise Exception(u"未知的rank_type:{}".format(rank_type))
        url = 'https://c.y.qq.com{}'.format(path)
        headers = {
            'method': 'GET',
            'authority': 'c.y.qq.com',
            'schema': 'https',
            'path': path,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh-TW;q=0.6',
            'Referer': 'https://y.qq.com/n/yqq/toplist/26.html',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
        }
        import pdb
        pdb.set_trace()
        try:
            res = self.openUrl(url, headers=headers)
            import pdb
            pdb.set_trace()
            rj = json.loads(res.strip().replace('MusicJsonCallbacktoplist', '')[1:-1].strip())

            song_list = rj['songlist']
            if len(song_list) == 0:
                raise Exception("len(song_list) == 0")
            songs = []
            song_tasks = []
            rank_songs = []
            index = page * song_num + 1
            for _s in song_list:
                _d = _s['data']

                # print _d['songname']

                # hot songs
                rank_song = {
                    'url': index,
                    'name': _d['songname'],
                    'mid': _d['songmid'],
                }
                rank_songs.append(rank_song)

                # 新增song_task
                song_task = {
                    "status": 0,
                    "last_crawl_time": 0,
                    "name": _d['songname'],
                    "url": "https://y.qq.com/n/yqq/song/%s.html" % _d['songmid'],
                    "mid": _d['songmid']
                }
                song_tasks.append(song_task)

                # 新增song
                song = {}
                song['is_to_mysql'] = 0
                song['mus_Name'] = _d['songname']  # 歌曲
                song['url'] = 'https://y.qq.com/n/yqq/song/{}.html'.format(_d['songmid'])
                song['mid'] = _d['songmid']
                song['mus_Singer'] = [{'name': s['name'], 'mid': s['mid']} for s in _d['singer']]  # 歌手 是列表
                song['mus_Album'] = _d['albumname']  # 专辑
                song['album_mid'] = _d['albummid']
                song['album_url'] = 'https://y.qq.com/n/yqq/album/{}.html'.format(_d['albummid'])
                song['mus_Time'] = _d['interval']  # 时长
                songs.append(song)

                index += 1

            import pdb
            pdb.set_trace()
            # update song
            self.sock.insert_data_if_not_exist(self.dbName, "%s_song" % self.siteName, songs)
            # put song tasks
            self.sock.put_task(self.dbName, "%s_song_tasks" % self.siteName, song_tasks)
            # put rank songs
            self.sock.insert_data(self.dbName, rank_type, rank_songs)
            self.logger.info("finish to crawl {} , page:{}".format(rank_type, page))
        except Exception as e:
            trace = traceback.format_exc()
            info = 'error:{},trace:{}'.format(str(e), trace)
            self.logger.warning(info)

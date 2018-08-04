# coding:utf8
import copy
import json
import time

import requests
from pymongo import MongoClient

uname = 'songs_user'
passwd = 'songs2018'
host = '127.0.0.1'
port = 27017
the_db = 'songs'
mc = MongoClient(host, port)
db = mc[the_db]
db.authenticate(uname, passwd)


def crawl_song(_url):
    """
    抓取歌曲详情和歌词
    :param _url:
    :return:
    """

    _headers = {
        'method': 'GET',
        'authority': 'c.y.qq.com',
        'scheme': 'https',
        'Referer': _url,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh-TW;q=0.6',
    }

    print(_url)
    mid = _url.split('/')[-1].split('.html')[0]

    # 抓取歌曲详情
    path = '/v8/fcg-bin/fcg_play_single_song.fcg?songmid={}&tpl=yqq_song_detail&format=jsonp&callback=getOneSongInfoCallback&g_tk=5381&jsonpCallback=getOneSongInfoCallback&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0'.format(
        mid)
    url = 'https://c.y.qq.com{}'.format(path)
    headers = copy.deepcopy(_headers)
    headers['path'] = path

    res0 = requests.get(url, headers=headers)
    # print(res0.text)

    rt = res0.text.replace('getOneSongInfoCallback(', '').replace(')', '')
    rj = json.loads(rt)
    print(rj)

    music_id = rj['data'][0]['id']
    name = rj['data'][0]['name']
    singers = rj['data'][0]['singer']
    singers = [s['name'] for s in singers]

    # 抓取歌曲详情
    path = '/lyric/fcgi-bin/fcg_query_lyric.fcg?nobase64=1&musicid={}&callback=jsonp1&g_tk=5381&jsonpCallback=jsonp1&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0'.format(
        music_id)
    url = 'https://c.y.qq.com{}'.format(path)
    headers = copy.deepcopy(_headers)
    headers['path'] = path

    res1 = requests.get(url, headers=headers)
    # print(res1.text)

    rt = res1.text.replace('jsonp1(', '').replace(')', '')
    rj = json.loads(rt)
    print(rj)
    lyric = rj['lyric']

    song = {
        'name': name,
        'music_id': music_id,
        'url': _url,
        'mid': mid,
        'singers': singers,
        'lyric': lyric,
    }
    return song


def crawl_singer(_url):
    """

    :param _url:
    :return:
    """
    singermid = _url.split('/')[-1].split('.')[0]
    _t = int(time.time() * 1000)
    path = '/splcloud/fcgi-bin/fcg_get_singer_desc.fcg?singermid={}&utf8=1&outCharset=utf-8&format=xml&r={}'.format(
        singermid, _t)

    headers = {
        'method': 'GET',
        'authority': 'c.y.qq.com',
        'scheme': 'https',
        'path': path,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
        'accept': '*/*',
        'referer': _url,
        'accept-encoding': '',
        'accept-language': 'zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7,zh-TW;q=0.6',
    }

    url = 'https://c.y.qq.com{}'.format(_url)

    res0 = requests.get(url, headers=headers)


    return

def crawl_album(self):
    """抓取专辑"""
    return

def crawl_album_list(self):
    """抓取专辑列表"""
    return

def run():
    urls = [
        'https://y.qq.com/n/yqq/song/003FFWnA3AIczD.html',
        'https://y.qq.com/n/yqq/song/001Qu4I30eVFYb.html',
    ]
    for url in urls:
        song = crawl_song(url)
        print(song)
        _url = 'http://127.0.0.1:5000/insert_data?data={}'.format(song)
        res = requests.get(_url)
        print(res.text)
        # if not db['new_songs'].find_one({'url': song['url']}):
        #     db['new_songs'].insert_one(song)

    for item in db['new_songs'].find():
        print(item['name'])


if __name__ == '__main__':
    run()

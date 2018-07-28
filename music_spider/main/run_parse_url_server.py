# encoding: utf-8
"""
@author: xsren 
@contact: bestrenxs@gmail.com
@site: xsren.me

@version: 1.0
@license: Apache Licence
@file: run_parse_url_server.py
@time: 2017/6/10 下午9:03

"""
import copy
import json
import logging
import random
import re
import time
import traceback
from functools import wraps

import pymongo
import requests
from flask import Flask, request, jsonify, Response, make_response

import settings
app = Flask(__name__)


class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt=None):
        logging.Formatter.__init__(self, fmt=fmt)

    def format(self, record):
        COLORS = {
            'Black': '0;30',
            'Red': '0;31',
            'Green': '0;32',
            'Brown': '0;33',
            'Blue': '0;34',
            'Purple': '0;35',
            'Cyan': '0;36',
            'Light_Gray': '0;37',

            'Dark_Gray': '1;30',
            'Light_Red': '1;31',
            'Light_Green': '1;32',
            'Yellow': '1;33',
            'Light_Blue': '1;34',
            'Light_Purple': '1;35',
            'Light_Cyan': '1;36',
            'White': '1;37',
        }
        COLOR_SEQ = "\033[%sm"
        RESET_SEQ = "\033[0m"

        message = logging.Formatter.format(self, record)

        if record.levelno == logging.DEBUG:
            message = COLOR_SEQ % COLORS['Green'] + message + RESET_SEQ
        elif record.levelno == logging.INFO:
            # message = COLOR_SEQ % COLORS['White'] + message + RESET_SEQ
            pass
        elif record.levelno == logging.WARNING:
            message = COLOR_SEQ % COLORS['Brown'] + message + RESET_SEQ
        elif record.levelno == logging.ERROR:
            message = COLOR_SEQ % COLORS['Red'] + message + RESET_SEQ
        elif record.levelno == logging.CRITICAL:
            message = COLOR_SEQ % COLORS['Purple'] + message + RESET_SEQ
        return message


import logging.handlers

logger = logging.getLogger("run_parse_url_server")
logger.setLevel(logging.DEBUG)

# file
log_file_name = "run_parse_url_server.log"
fh = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=1024 * 1024 * 1024, backupCount=1)
color_formatter = ColoredFormatter(fmt='%(asctime)s %(funcName)s[line:%(lineno)d] [%(levelname)s]: %(message)s')
fh.setFormatter(color_formatter)

fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

# stdout
sh = logging.StreamHandler()
color_formatter = ColoredFormatter(fmt='%(asctime)s %(funcName)s[line:%(lineno)d] [%(levelname)s]: %(message)s')
sh.setFormatter(color_formatter)
sh.setLevel(logging.DEBUG)
logger.addHandler(sh)


def allow_cross_domain(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        rst = make_response(fun(*args, **kwargs))
        rst.headers['Access-Control-Allow-Origin'] = '*'
        rst.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
        allow_headers = "Referer,Accept,Origin,User-Agent,x-requested-with,content-type"
        rst.headers['Access-Control-Allow-Headers'] = allow_headers
        return rst

    return wrapper_fun


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL, need token.\n', 403,
        {'WWW-Authenticate': 'Basic realm="token Required"'})


def get_db():
    mongo_url = "mongodb://{}:{}@{}:{}/{}".format(
        settings.mongo_user,
        settings.mongo_passwd,
        settings.mongo_host,
        settings.mongo_port,
        settings.auth_db,
    )
    mc = pymongo.MongoClient(mongo_url)
    db = mc["songs"]
    return db


db = get_db()

proxies = {
    "http": "http://forward.xdaili.cn:80",
    "https": "http://forward.xdaili.cn:80",
}


def md5(data):
    import hashlib
    hash_md5 = hashlib.md5(data)
    md5_res = hash_md5.hexdigest()
    return md5_res


order_num = "ZF20181179125ew3gDZ"
secret = "e0263081c9ea4a9e8aaadf7a093dd510"


def get_auth_header():
    """获取讯代理认证IP"""
    t = int(time.time())
    plan_text = "orderno={},secret={},timestamp={}".format(order_num, secret, t)
    sign = md5(plan_text).upper()
    header = "sign={}&orderno={}&timestamp={}".format(sign, order_num, t)
    return header


def get_real_path(_url):
    # 内部歌曲
    if _url.startswith('https://kk-qq-song.') or _url.startswith('http://kk-qq-song.'):
        return 0, _url
    if not re.search(r'https://y\.qq\.com/n/yqq/song/.*\.html', _url):
        return 2, "invalid url"
    mid = _url.split("https://y.qq.com/n/yqq/song/")[-1].split(".html")[0]

    '''**********************************************************************'''
    # 应对有的mid和不正确的问题
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'c.y.qq.com',
        'Referer': _url,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
    }

    _url_1 = 'https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg?songmid=%s&tpl=yqq_song_detail&format=jsonp&g_tk=5381&loginUin=0&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0' % mid
    try:
        res_1 = requests.get(_url_1, headers=headers)
        logger.debug("{}".format(_url_1))
        rj_1 = json.loads(res_1.text[1:-1])
        data = rj_1['data'][0]
        s_mid = data['file']['media_mid']
    except Exception as e:
        err = "error:{}, trace:{}".format(str(e), traceback.format_exc())
        logger.error(err)
        return 5, "network error, please retry"

    '''**********************************************************************'''

    cb = random.randint(10000000000000000, 999999999999999999)
    guid = random.randint(1000000000, 9999999999)
    path = "/base/fcgi-bin/fcg_music_express_mobile3.fcg?g_tk=5381&jsonpCallback=MusicJsonCallback%s&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&cid=205361747&callback=MusicJsonCallback%s&uin=0&songmid=%s&filename=C400%s.m4a&guid=%s" % (
        cb, cb, mid, s_mid, guid)
    headers = {
        'method': 'GET',
        'authority': 'c.y.qq.com',
        'scheme': 'https',
        'path': path,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'accept': '*/*',
        'referer': 'https://y.qq.com/portal/player.html',
        'accept-encoding': 'gzip, deflate, sdch, br',
        'accept-language': 'zh-CN,zh;q=0.8',
    }
    url = "https://c.y.qq.com%s" % path
    try_times = 0
    while try_times < 3:
        try_times += 1
        try:
            if try_times == 3:
                res = requests.get(url, headers=headers, timeout=1.5)
            else:
                _headers = copy.deepcopy(headers)
                _headers['Proxy-Authorization'] = get_auth_header()
                # res = requests.get(url, headers=_headers, timeout=1, verify=False)
                res = requests.get(url, headers=_headers, timeout=1.5, proxies=proxies, verify=False)
            if res.status_code != 200:
                return 3, "server error, please contact admin"
            text = res.text.split('(')[-1].split(')')[0]
            rj = json.loads(text)
            logger.debug("{}".format(rj))
            vkey = rj['data']['items'][0]['vkey']
            filename = rj['data']['items'][0]['filename']
            # 有一部分数据居然有重定向。。。暂时不管了。。
            if vkey is None or vkey == "":
                info = u"版权问题。。。,url:{}".format(_url)
                logger.warning(info)
                # return 4, "copyright problem"
                continue
                # raise Exception("vkey is None...")
            if rj['data']['items'][0]['subcode'] != 0:
                err = "server error, please contact admin"
                logger.error(err)
                # return 3, err
                continue
            real_url = "http://dl.stream.qqmusic.qq.com/%s?vkey=%s&guid=%s&uin=0&fromtag=66" % (
                filename, vkey, guid)
            logger.info("real_url:{}".format(real_url))
            return 0, real_url
        except Exception as e:
            # return 5, "network error, please retry"
            logger.error(str(e))
    return 4, "copyright problem"


def update_song_status(url, is_free):
    db['qq_song'].update_one({'url': url}, {'$set': {'is_to_mysql': 0, 'isFree': is_free}})


def auth(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        token = request.args.get("token", None)
        if db.find_token(token):
            return fun(*args, **kwargs)
        else:
            return authenticate()

    return wrapper_fun


@app.route('/parse')
# @auth
@allow_cross_domain
def parse():
    url = request.args.get('url', None)
    if url:
        url = url.encode('utf8')
        logger.debug("begin to parse url:{}".format(url))
        status, data = get_real_path(url)
        if status == 0:
            logger.debug("finish to parse url:{},status:{}".format(url, status))
            return jsonify({'status': status, 'info': 'ok', 'data': data})
        else:
            logger.debug("finish to parse url:{},status:{},data:{}".format(url, status, data))
            return jsonify({'status': status, 'info': data})
    else:
        return jsonify({'status': 1, 'info': 'param not enough'})


@app.route('/update_status')
# @auth
def update_status():
    url = request.args.get('url', None)
    is_free = request.args.get('isFree', None)
    if url and is_free:
        update_song_status(url, is_free)
        return jsonify({'status': 0, 'info': 'ok'})
    else:
        return jsonify({'status': 1, 'info': 'param not enough'})


@app.route('/get_rank_songs')
# @auth
def get_rank_songs():
    ranks = ["hot_songs", "new_songs"]
    data = {}
    try:
        for rank in ranks:
            songs = []
            for item in db[rank].find().limit(100):
                song = {
                    'index': item['url'],
                    'mid': item['mid'],
                }
                songs.append(song)
            data[rank] = songs
        return jsonify({'status': 0, 'info': 'ok', 'data': data})
    except Exception as e:
        trace = traceback.format_exc()
        info = 'error:{},trace:{}'.format(str(e), trace)
        logger.warning(info)
        return jsonify({'status': 1, 'info': str(e)})


@app.route('/get_rank_playlist')
# @auth
def get_rank_playlist():
    ranks = ["new_playlist", "recommend_playlist"]
    data = {}
    try:
        for rank in ranks:
            songs = []
            for item in db[rank].find().limit(100):
                song = {
                    'index': item['url'],
                    'dissid': item['dissid'],
                }
                songs.append(song)
            data[rank] = songs
        return jsonify({'status': 0, 'info': 'ok', 'data': data})
    except Exception as e:
        trace = traceback.format_exc()
        info = 'error:{},trace:{}'.format(str(e), trace)
        logger.warning(info)
        return jsonify({'status': 1, 'info': str(e)})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5023, debug=False)

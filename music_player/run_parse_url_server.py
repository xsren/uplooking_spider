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
import json
import logging
import random
import re
import traceback

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def md5(data):
    import hashlib
    hash_md5 = hashlib.md5(data)
    md5_res = hash_md5.hexdigest()
    return md5_res


def get_real_path(_url):
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
            res = requests.get(url, headers=headers, timeout=1.5)
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


@app.route('/parse')
def parse():
    url = request.args.get('url', None)
    if url:
        # url = url.encode('utf8')
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


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5023, debug=True)

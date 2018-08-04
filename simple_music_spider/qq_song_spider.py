# coding:utf8
import json
import re
import time

import requests
from mongo_handler import get_db

db = get_db()


def crawl_song(self, t):
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

def run():
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


if __name__ == '__main__':
    run()
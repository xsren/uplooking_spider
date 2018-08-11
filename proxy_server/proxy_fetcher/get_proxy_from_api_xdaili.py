# coding:utf-8
from gevent import monkey

monkey.patch_all()
import requests
import pymongo
import gevent
from gevent import queue
import chardet
from pymongo import ReplaceOne
import time

mongo_url = 'mongodb://127.0.0.1'
client = pymongo.MongoClient(mongo_url, connect=False)
db = client["dianping"]
coll = db["proxys"]

sites = []


def get_proxy():
    try:
        url = 'http://api.xdaili.cn/xdaili-api//privateProxy/applyStaticProxy?spiderId=925a4bd70dfa4f3dbda91d287afaf8db&returnType=2&count=1'
        res = requests.get(url)
        rj = res.json()
        if rj['ERRORCODE'] != "0":
            time.sleep(3)
            return []
        ps = rj['RESULT']
        print('get proxy num:%s' % len(ps))
        proxies = []
        for p in ps:
            proxy = {
                'ip': p['ip'],
                'port': int(p['port'])
            }
            proxies.append(proxy)
        if len(proxies) == 0:
            time.sleep(3)
        return proxies
    except Exception as e:
        print('error:%s......' % str(e))
        time.sleep(3)
        return []


def check_proxy(proxies):
    # 检查数据库是否存在
    exists = [r['ip'] for r in coll.find({"ip": {"$in": list(set([t['ip'] for t in proxies]))}}, {'ip': 1})]
    spawns = []
    q = queue.Queue()
    for p in proxies:
        if p['ip'] not in exists:
            spawns.append(gevent.spawn(baidu_check, p, q))

    print('new ip num:%s' % len(spawns))

    # 检查网络可用性
    MAX_CURRENT_NUM = 20
    t0 = time.time()
    while True:
        if len(spawns) > MAX_CURRENT_NUM:
            gevent.joinall(spawns[:MAX_CURRENT_NUM])
            spawns = spawns[MAX_CURRENT_NUM:]
        else:
            gevent.joinall(spawns)
            break

    print(time.time() - t0)

    ok_ps = []
    while True:
        try:
            p = q.get_nowait()
            ok_ps.append(p)
        except Exception as e:
            print(str(e))
            break

    print('ok ip num:%s' % len(ok_ps))
    return ok_ps


def baidu_check(p, q):
    proxies = {"http": "http://%s:%s" % (p['ip'], p['port']), "https": "https://%s:%s" % (p['ip'], p['port'])}
    try:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch, br',
            'Accept-Language': 'zh,en-US;q=0.8,en;q=0.6,zh-CN;q=0.4,zh-TW;q=0.2',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'www.baidu.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36',
        }
        r = requests.get(url='https://www.baidu.com', headers=headers, timeout=5, proxies=proxies)
        # r = requests.get(url='https://angel.co/directory/companies/b', headers=config.get_header(), timeout=config.TIMEOUT, proxies=proxies)
        r.encoding = chardet.detect(r.content)['encoding']
        if r.ok:
            q.put(p)
    except Exception as e:
        # print str(e)
        pass


def save_proxy(ok_ps):
    ns = []
    for ok in ok_ps:
        ok['last_use_time'] = 0
        ok['protocol'] = 0
        ok['is_own'] = 1
        ok['is_ok'] = 0
        ns.append(ReplaceOne({'ip': ok['ip']}, ok, upsert=True))

    if len(ns) > 0:
        res = coll.bulk_write(ns)
        print('upsert count:%s' % res.upserted_count)


def run():
    while True:
        try:
            num = coll.count({'protocol': 0, 'is_ok': 0})
            print('now proxy num:%s' % num)
            if num > 100:
                time.sleep(3)
            else:
                proxies = get_proxy()
                ok_ps = check_proxy(proxies)
                save_proxy(ok_ps)
        except Exception as e:
            print(str(e))
            time.sleep(3)


if __name__ == '__main__':
    run()

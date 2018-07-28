# coding:utf8

import sys
import time
import traceback
from queue import Queue

from pymongo import UpdateOne, ReplaceOne, InsertOne, UpdateMany
from pymongo.errors import BulkWriteError
from twisted.internet import reactor, defer

# 本地库
sys.path.append('../main')
import settings
import common


class DbManager:
    def __init__(self, logger, mc, write_queues, task_queues, count_queue):
        self.logger = logger
        self.mc = mc
        self.write_queues = write_queues
        self.task_queues = task_queues
        self.count_queue = count_queue

    def init_write_queue(self, dbName, collName):
        if self.write_queues.get(dbName, None) == None:
            self.write_queues[dbName] = {}
            self.write_queues[dbName][collName] = Queue(maxsize=settings.write_queue_size)
        else:
            if self.write_queues[dbName].get(collName, None) == None:
                self.write_queues[dbName][collName] = Queue(maxsize=settings.write_queue_size)

    def init_task_queue(self, dbName, collName):
        if self.task_queues.get(dbName, None) == None:
            self.task_queues[dbName] = {}
            self.task_queues[dbName][collName] = Queue(maxsize=settings.write_queue_size)
        else:
            if self.task_queues[dbName].get(collName, None) == None:
                self.task_queues[dbName][collName] = Queue(maxsize=settings.write_queue_size)

    '''
    一般网站公用的处理代码 common
    '''

    def cleanup_handle_queue(self):
        self.logger.info("clear ... cleanup begin")
        try:
            reactor.callInThread(self._handle_write_queue, 1)
            # self._handle_write_queue(limit=1)
            self._handle_count_queue(limit=1)
        except BulkWriteError as bwe:
            self.logger.error(bwe.details)
            # you can also take this component and do more analysis
            werrors = bwe.details['writeErrors']
            self.logger.error(werrors)
        except Exception as e:
            self.logger.error(str(e))
            traceback.print_exc()

        self.logger.info("clear ... cleanup end")

    def _handle_write_queue(self, limit):
        for dbName, v in self.write_queues.items():
            for collName, _queue in v.items():
                if _queue.qsize() >= limit:
                    t0 = time.time()
                    requests, dups = [], []
                    qsize = _queue.qsize()
                    while _queue.qsize() > 0:
                        try:
                            tup = _queue.get_nowait()
                            _queue.task_done()
                        except Exception as e:
                            self.logger.error(str(e))
                            break
                        if tup[0] in dups:
                            continue
                        else:
                            dups.append(tup[0])
                            requests.append(tup[1])
                    if len(requests) > 0:
                        self.mc[dbName][collName].bulk_write(requests)
                    t_diff = time.time() - t0
                    info = "handle_write_queue,db:%s,coll:%s,size:%s,t_diff:%s" % (dbName, collName, qsize, t_diff)
                    self.logger.info(info)

    def _handle_count_queue(self, limit):
        if self.count_queue.qsize() >= limit:
            t0 = time.time()
            requests = []
            qsize = self.count_queue.qsize()
            while self.count_queue.qsize() > 0:
                try:
                    tmp = self.count_queue.get_nowait()
                    self.count_queue.task_done()
                except Exception as e:
                    self.logger.error(str(e))
                    break
                requests.append(tmp)
            if len(requests) > 0:
                self.mc[settings.count_db_name][settings.count_coll_name].bulk_write(requests)

            t_diff = time.time() - t0
            info = "handle_count_queue,size:%s,t_diff,%s" % (qsize, t_diff)
            self.logger.info(info)

    @defer.inlineCallbacks
    def _common_put_task_to_db(self, dbName, collName, data):
        t0 = time.time()
        self.init_write_queue(dbName, collName)

        # 统计
        res = yield self.mc[dbName][collName].find({"url": {"$in": list(set([t['url'] for t in data]))}}, {'url': 1})
        exists = [r['url'] for r in res]
        self.saveCountData(dbName, collName, common.NEW_TASK, len(data) - len(exists))
        # 更新数据
        for t in data:
            if t["url"] not in exists:
                self.write_queues[dbName][collName].put((t['url'], InsertOne(t)))

        t_diff = time.time() - t0
        info = "%s, %s, %s" % (dbName, collName, t_diff)
        self.logger.debug(info)
        defer.returnValue([])

    @defer.inlineCallbacks
    def _common_get_task_from_db(self, dbName, collName, count):
        t0 = time.time()
        self.init_task_queue(dbName, collName)
        info = '%s, %s, qsize:%s' % (dbName, collName, self.task_queues[dbName][collName].qsize())
        self.logger.debug(info)
        if self.task_queues[dbName][collName].qsize() <= 0:
            t1 = time.time()
            tasks = yield self.mc[dbName][collName].find({'status': common.NOT_CRAWL},
                                                         limit=count * 10)  # .limit(settings.get_tasks_num_one_time)
            # tasks = self.mc[dbName][collName].find({'status':common.NOT_CRAWL}, limit=settings.get_tasks_num_one_time)
            requests, ts = [], []
            for task in tasks:
                requests.append(
                    UpdateMany({'url': task["url"]}, {"$set": {"status": common.CRAWLING, "last_crawl_time": 0}}))
                task.pop('_id')
                ts.append(task)
            if len(requests) > 0:
                # self.mc[dbName][collName].bulk_write(requests)
                yield self.mc[dbName][collName].bulk_write(requests)
            for t in ts:
                self.task_queues[dbName][collName].put(t)
            t_diff = time.time() - t1
            info = "query mongo, %s, %s, get:%s, use time:%s" % (dbName, collName, len(ts), t_diff)
            self.logger.debug(info)
        ts = []
        for x in range(count):
            try:
                t = self.task_queues[dbName][collName].get_nowait()
                self.task_queues[dbName][collName].task_done()
                ts.append(t)
            except:
                # self.logger.error(str(e))
                continue
        t_diff = time.time() - t0
        info = "total, %s, %s, return : %s , use time : %s" % (dbName, collName, len(ts), t_diff)
        self.logger.debug(info)
        defer.returnValue(ts)

    def _common_change_task_status(self, dbName, collName, data):
        t0 = time.time()
        self.init_write_queue(dbName, collName)

        # 统计
        success = [t['url'] for t in data if t['status'] == common.CRAWL_SUCCESS]
        self.saveCountData(dbName, collName, common.ONE_TASK, len(success))
        # 更新数据
        for t in data:
            # self.logger.debug('url:%s,status:%s'%(t['url'],t['status']))
            self.write_queues[dbName][collName].put(
                (t['url'],
                 UpdateMany({'url': t['url']},
                            {"$set": {'status': t['status'],
                                      'last_crawl_time': time.time()
                                      }})
                 )
            )

        t_diff = time.time() - t0
        info = "%s, %s, %s" % (dbName, collName, t_diff)
        self.logger.debug(info)

    def _common_put_data_to_db(self, dbName, collName, data):
        """为了性能，使用的是eplace方法"""
        t0 = time.time()
        self.init_write_queue(dbName, collName)

        # 统计
        self.saveCountData(dbName, collName, common.ONE_DATA, len(data))
        # 
        for t in data:
            t['crawl_time'] = time.time()
            self.write_queues[dbName][collName].put((t['url'], ReplaceOne({'url': t['url']}, t, upsert=True)))

        t_diff = time.time() - t0
        info = "%s, %s, %s" % (dbName, collName, t_diff)
        self.logger.debug(info)

    def _common_insert_data_if_not_exist(self, dbName, collName, data):
        """如果数据不存在则插入，否则pass"""
        t0 = time.time()
        for t in data:
            if not self.mc[dbName][collName].find_one({'url': t['url']}):
                t['crawl_time'] = time.time()
                self.mc[dbName][collName].insert_one(t)
        t_diff = time.time() - t0
        info = "%s, %s, %s" % (dbName, collName, t_diff)
        self.logger.debug(info)

    def _common_update_data(self, dbName, collName, data):
        """更新数据"""
        t0 = time.time()
        self.init_write_queue(dbName, collName)

        for t in data:
            t['crawl_time'] = time.time()
            self.write_queues[dbName][collName].put((t['url'],
                                                     UpdateOne({'url': t['url']}, t, upsert=True)))

        t_diff = time.time() - t0
        info = "%s, %s, %s" % (dbName, collName, t_diff)
        self.logger.debug(info)

    # 存储统计数据
    def saveCountData(self, dbName, collName, _type, count):
        date = time.strftime("%Y-%m-%d", time.localtime())
        # 网站
        u1 = UpdateOne({'date': date, 'dbName': dbName, 'collName': collName, "_type": _type},
                       {'$inc': {'total': count}}, upsert=True)
        # 总体
        u2 = UpdateOne({'date': date, 'dbName': "all", 'collName': "all", "_type": _type}, {'$inc': {'total': count}},
                       upsert=True)
        self.count_queue.put(u1)
        self.count_queue.put(u2)


if __name__ == '__main__':
    pass

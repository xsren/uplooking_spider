# coding:utf8
import atexit
import struct
# from threading import Thread
import sys
import threading
import time
from queue import Queue

import msgpack
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol

sys.path.append('../common')
import DbManager
import utils
import settings
import common


class ServerProtocal(Protocol):
    def __init__(self, users, logger, db):
        self.users = users
        self.logger = logger
        self.db = db
        self.name = None
        self.state = "FIRST"
        self.buffer = b''
        self.data_lenth = 0

    def connectionMade(self):
        info = "connection from", self.transport.getPeer()
        self.logger.debug(info)

    def connectionLost(self, reason):
        info = "Lost connection from", self.transport.getPeer(), reason.getErrorMessage()
        self.logger.warning(info)
        if self.name in self.users:
            del self.users[self.name]

    def dataReceived(self, data):
        if self.state == "FIRST":
            self.handle_FIRST(data)
        else:
            self.handle_DATA(data)

    # 验证密码
    def handle_FIRST(self, data):
        tmp = data.split(b'@@@***')
        if len(tmp) < 2:
            self.transport.abortConnection()
        else:
            name = tmp[0].decode('utf8')
            pwd = tmp[1].decode('utf8')
            if utils.md5(name + settings.tcp_login_key) == pwd:
                self.name = name
                self.users[name] = self
                self.state = "DATA"
                self.transport.write(b"OK!!")
            else:
                self.transport.abortConnection()

    def handle_DATA(self, data):
        # self.logger.info('data length:%s'%len(data))

        self.buffer += data
        while True:
            if self.data_lenth <= 0:
                if len(self.buffer) >= 4:
                    self.data_lenth = struct.unpack('>I', self.buffer[:4])[0]
                    if self.data_lenth > 1024 * 1024:
                        utils.send_email("data length:%s" % self.data_lenth)
                        self.transport.abortConnection()
                    self.buffer = self.buffer[4:]
                else:
                    return
            if len(self.buffer) >= self.data_lenth:
                tmp_data = self.buffer[:self.data_lenth]
                self.buffer = self.buffer[self.data_lenth:]
                self.data_lenth = 0
                self.process_data(tmp_data)
                return
            else:
                return

    def process_data(self, data):
        rj = msgpack.unpackb(data, encoding="utf8")
        if rj == 'echo':
            return
        if rj['type'] == common.REQUEST_MESSAGE:
            dbName = rj["dbName"]
            collName = rj["collName"]
            action = rj["action"]
            data = rj["data"]
            self.handle_request(dbName, collName, action, data)

        elif rj['type'] == common.ECHO_MESSAGE:
            pass
        else:
            info = "not support message:%s" % rj['type']
            self.logger.warning(info)
            self.transport.abortConnection()

    def send_msg(self, msg):
        msg = struct.pack('>I', len(msg)) + msg
        self.mysend(msg)

    def mysend(self, msg):

        totalsent = 0
        MSGLEN = len(msg)
        while totalsent < MSGLEN:
            if len(msg) > 4:
                self.transport.write(msg[:4])
                msg = msg[4:]
            else:
                self.transport.write(msg)
            totalsent = totalsent + 4

    def handle_request(self, dbName, collName, action, data):
        db = self.db
        if action == common.PUT_TASK:
            d = db._common_put_task_to_db(dbName, collName, data)
            d.addCallback(self.handle_success)
            d.addErrback(self.handle_failure)
        elif action == common.GET_TASK:
            d = db._common_get_task_from_db(dbName, collName, data['count'])
            d.addCallback(self.handle_success)
            d.addErrback(self.handle_failure)
        elif action == common.PUT_DATA:
            db._common_put_data_to_db(dbName, collName, data)
            self.handle_success([])
        elif action == common.CHANGE_TASK_STATUS:
            db._common_change_task_status(dbName, collName, data)
            self.handle_success([])
        elif action == common.UPDATE_DATA:
            db._common_update_data(dbName, collName, data)
            self.handle_success([])
        elif action == common.INSERT_DATA_IF_NOT_EXIST:
            db._common_insert_data_if_not_exist(dbName, collName, data)
            self.handle_success([])

    def handle_success(self, res):
        res = {
            '_type': common.RESPONSE_MESSAGE,
            'status': common.OK,
            'fromAddr': 'server',
            'toAddr': self.name,
            'data': res,
        }
        _res = msgpack.packb(res)
        self.send_msg(_res)

    def handle_failure(self, err):
        res = {
            '_type': common.RESPONSE_MESSAGE,
            'status': common.FAIL,
            'fromAddr': 'server',
            'toAddr': self.name,
            'data': [],
        }
        _res = msgpack.packb(res)
        self.send_msg(_res)
        self.logger.error(err)


class ServerFactory(Factory):
    def __init__(self):
        self.users = {}
        write_queues = {}
        task_queues = {}
        count_queue = Queue(maxsize=settings.count_queue_size)

        mc = settings.getMCInstance(isTxMongo=False)
        self.logger = utils.initLogger('%s/run_data_server_main.log' % settings.logs_dir_home)
        self.db = DbManager.DbManager(self.logger, mc, write_queues, task_queues, count_queue)

        # 开一个线程定时清理
        ts = []
        t1 = threading.Thread(target=self.sched_cleanup, args=())
        ts.append(t1)
        for t in ts:
            t.setDaemon(True)
            t.start()

        self.logger.info("__init__ finish")

    def buildProtocol(self, addr):
        return ServerProtocal(self.users, self.logger, self.db)

    # 定时清理
    def sched_cleanup(self):
        while True:
            time.sleep(10)
            self.cleanup()

    def cleanup(self):
        self.db.cleanup_handle_queue()


if __name__ == '__main__':
    port = 2234
    factory = ServerFactory()
    print("run server on %s" % port)
    reactor.listenTCP(port, factory)
    reactor.run()
    # 退出时做清理工作
    atexit.register(factory.cleanup)

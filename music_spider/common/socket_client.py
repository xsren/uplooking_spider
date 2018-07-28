# coding:utf8

# 系统库

import json
import socket
import struct
import time

import common
import msgpack
# 本地库
import utils


class SocketClient():
    def __init__(self, host, port, key, user_name, lock=None, logger=None):
        self.host = host
        self.port = port
        self.key = key
        self.user_name = user_name
        self.lock = lock
        self.logger = logger
        self.isConnected = False
        self.connect()
        self.one_time_send = 1024  # 一次只发生1个字节，否则在高并发情况下会报错
        self.server_has_task_to_crawl = True
        self.is_waiting_get_task_res = False
        self.url = 'http://%s:%s/crawler' % (host, port)

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(60 * 10)
        except Exception as e:
            if self.logger:
                self.logger.error(str(e))
            print(str(e))
            self.isConnected = False
            self.reconnect_without_lock(sleep_time=60)
            return

        self.auth()

    # server端需要认证
    def auth(self):
        password = utils.md5(self.user_name + self.key)
        try:
            data = "%s@@@***%s" % (self.user_name, password)
            self.sock.sendall(data.encode('utf8'))
            res = self.recvall(4)
            if res != b'OK!!':
                if self.logger:
                    self.logger.error("invalid password!!!")
                else:
                    print("invalid password!!!")
                self.isConnected = False
                self.reconnect_without_lock(sleep_time=30)
                return
            self.isConnected = True
        except Exception as e:
            if self.logger:
                self.logger.error(str(e))
            else:
                print
                str(e)
            self.isConnected = False
            self.reconnect(sleep_time=30)
            return

    def reconnect_without_lock(self, sleep_time=15):
        self.__del__()
        time.sleep(sleep_time)
        self.connect()

    def reconnect(self, sleep_time=15):
        if self.lock:
            self.lock.acquire()
        if self.logger:
            self.logger.warning("reconnecting......")
        else:
            print
            "reconnecting......"
        if self.isConnected == False:
            self.__del__()
            time.sleep(sleep_time)
            self.connect()
        if self.logger:
            self.logger.warning("finish reconnect......")
        else:
            print
            "finish reconnect......"
        if self.lock:
            self.lock.release()

    def send_msg(self, msg):
        msg1 = struct.pack('>I', len(msg)) + msg
        try:
            self.mysend(msg1)
            if len(msg) - 4 - 4 > 0:
                if self.logger:
                    self.logger.info("send:%s" % (len(msg) - 4))
                else:
                    print
                    "send:%s" % (len(msg) - 4)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(str(e))
            else:
                print
                str(e)
            self.isConnected = False
            self.reconnect(sleep_time=60)
            return False

    def mysend(self, msg):
        totalsent = 0
        MSGLEN = len(msg)

        while totalsent < MSGLEN:
            if len(msg) > self.one_time_send:
                # sent = self.sock.send(msg[:self.one_time_send])
                # msg = msg[self.one_time_send:]
                sent = self.sock.send(msg)
                msg = msg[sent:]
            else:
                sent = self.sock.send(msg)
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def recv_msg(self):
        # Read message length and unpack it into an integer
        try:
            raw_msglen = self.recvall(4)
        except socket.timeout:
            if self.logger:
                self.logger.error('recv msg timeout ......')
            else:
                print
                'recv msg timeout ......'
            return None
        except Exception as e:
            self.logger.error(str(e))
            self.isConnected = False
            self.reconnect(sleep_time=60)
            return None

        if not raw_msglen:
            if self.logger:
                self.logger.warning("not raw_msglen")
            else:
                print
                "not raw_msglen"
            self.isConnected = False
            self.reconnect(sleep_time=60)
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data

        try:
            return self.recvall(msglen)
        except Exception as e:
            if self.logger:
                self.logger.error(str(e))
            else:
                print
                str(e)
            self.isConnected = False
            self.reconnect(sleep_time=60)
            return None

    def recvall(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            if n - len(data) > 4:
                packet = self.sock.recv(4)
            else:
                packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def send_echo(self):
        _echo = msgpack.packb('echo')
        self.send_msg(_echo)

    def get_task(self, dbName, collName, count=1):
        req = {
            'type': common.REQUEST_MESSAGE,
            'action': common.GET_TASK,
            'fromAddr': self.user_name,
            'toAddr': 'server',
            'dbName': dbName,
            'collName': collName,
            'data': {
                'count': count,
            }
        }
        _req = msgpack.packb(req)
        self.send_msg(_req)
        # time.sleep(0.5)
        while True:
            res = self.recv_msg()
            if res:
                return msgpack.unpackb(res)
            else:
                return None

    def insert_data(self, dbName, collName, data):
        req = {
            'type': common.REQUEST_MESSAGE,
            'action': common.PUT_DATA,
            'fromAddr': self.user_name,
            'toAddr': 'server',
            'dbName': dbName,
            'collName': collName,
            'data': data
        }
        _req = msgpack.packb(req)
        self.send_msg(_req)
        while True:
            res = self.recv_msg()
            if res:
                return
                # time.sleep(0.5)

    def update_data(self, dbName, collName, data):
        req = {
            'type': common.REQUEST_MESSAGE,
            'action': common.UPDATE_DATA,
            'fromAddr': self.user_name,
            'toAddr': 'server',
            'dbName': dbName,
            'collName': collName,
            'data': data
        }
        _req = msgpack.packb(req)
        self.send_msg(_req)
        while True:
            res = self.recv_msg()
            if res:
                return
                # time.sleep(0.5)

    def insert_data_if_not_exist(self, dbName, collName, data):
        req = {
            'type': common.REQUEST_MESSAGE,
            'action': common.INSERT_DATA_IF_NOT_EXIST,
            'fromAddr': self.user_name,
            'toAddr': 'server',
            'dbName': dbName,
            'collName': collName,
            'data': data
        }
        _req = msgpack.packb(req)
        self.send_msg(_req)
        while True:
            res = self.recv_msg()
            if res:
                return
                # time.sleep(0.5)

    def change_task_status(self, dbName, collName, data):
        req = {
            'type': common.REQUEST_MESSAGE,
            'action': common.CHANGE_TASK_STATUS,
            'fromAddr': self.user_name,
            'toAddr': 'server',
            'dbName': dbName,
            'collName': collName,
            'data': data
        }
        _req = msgpack.packb(req)
        self.send_msg(_req)
        while True:
            res = self.recv_msg()
            if res:
                return

    def put_task(self, dbName, collName, data):
        req = {
            'type': common.REQUEST_MESSAGE,
            'action': common.PUT_TASK,
            'fromAddr': self.user_name,
            'toAddr': 'server',
            'dbName': dbName,
            'collName': collName,
            'data': data
        }

        _req = msgpack.packb(req)
        self.send_msg(_req)
        while True:
            res = self.recv_msg()
            if res:
                return


if __name__ == '__main__':
    sc = SocketClient()
    sc.connect('127.0.0.1', 2234)
    sc.sock.sendall('aaa@@@***aaa')
    data = sc.recvall(4)
    print(data)
    print(len(data))
    dic = {}
    for i in range(10000):
        dic[i] = 'abcdefg' * 1000
    data = json.dumps(dic)
    print(len(data))
    sc.send_msg(struct.pack('>I', len(data)) + data)
    data = sc.recv_msg()
    print(data)
    print(len(data))
    sc.send_msg(data)

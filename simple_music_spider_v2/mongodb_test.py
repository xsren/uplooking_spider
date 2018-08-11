#coding:utf-8
from pymongo import MongoClient
from pymongo import InsertOne
import time

def test_insert():
    mc = MongoClient("127.0.0.1",maxPoolSize=None)
    db = mc['test']

    # 逐条写
    t0 = time.time()
    for i in range(0,100000):
        db['test_1'].insert_one({'_id':i,'x':1})
    print(time.time() - t0)

    time.sleep(1)

    # 批量写
    t0 = time.time()
    res =[]
    for i in range(0,100000):
        res.append(InsertOne({'_id':i,'x':1}))
    db['test_2'].bulk_write(res)
    print(time.time() - t0)


if __name__ == '__main__':
    test_insert()
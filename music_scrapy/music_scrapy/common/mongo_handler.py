# coding:utf8

from pymongo import MongoClient

def get_db():
    uname = 'songs_user'
    passwd = 'songs2018'
    host = '127.0.0.1'
    port = 27017
    the_db = 'songs'
    mc = MongoClient(host, port)
    db = mc[the_db]
    # db.authenticate(uname, passwd)
    return db

def run():
    pass


if __name__ == '__main__':
    run()
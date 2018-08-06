# coding:utf8
"""
https://github.com/nummy/pymongo-tutorial-cn
"""
import datetime

from pymongo import MongoClient

uname = 'songs_user'
passwd = 'songs2018'
host = '127.0.0.1'
port = 27017
the_db = 'songs'
mc = MongoClient(host, port)
db = mc[the_db]
db.authenticate(uname, passwd)


def run():
    post = {"author": "Mike",
            "text": "My first blog post!",

            "tags": ["mongodb", "python", "pymongo"],

            "date": datetime.datetime.utcnow()}

    db['posts'].insert_one(post)

    db['posts'].find_one()


if __name__ == '__main__':
    run()

# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient


class MusicScrapyPipeline(object):
    def __init__(self):
        uname = 'songs_user'
        passwd = 'songs2018'
        host = '127.0.0.1'
        port = 27017
        the_db = 'songs'
        mc = MongoClient(host, port)
        db = mc[the_db]
        # db.authenticate(uname, passwd)
        self._db = db

    def process_item(self, item, spider):
        import pdb
        pdb.set_trace()

        return item

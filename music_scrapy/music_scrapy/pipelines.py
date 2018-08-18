# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from music_scrapy.common.mongo_handler import get_db


class MusicScrapyFilePipeline(object):
    def process_item(self, item, spider):
        print("*" * 200)
        data = item['data']
        area = item['area']
        page = item['page']
        with open('tmp_{}_{}.txt'.format(area, page), 'w') as fh:
            fh.write(data.encode('utf8'))


class MusicScrapyMongodbPipeline(object):

    def __init__(self):
        self.db = get_db()

    def process_item(self, item, spider):
        print("@" * 200)
        coll_name = item['coll_name']
        data = item['data']
        self.db[coll_name].insert(data)
        return item

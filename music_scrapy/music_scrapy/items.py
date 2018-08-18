# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


def my_serializer(name):
    import pdb
    pdb.set_trace()
    return 'aaa:{}'.format(name)


class MusicScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field(serializer=my_serializer)
    mid = scrapy.Field()
    url = scrapy.Field()
    status = scrapy.Field()
    last_crawl_time = scrapy.Field()

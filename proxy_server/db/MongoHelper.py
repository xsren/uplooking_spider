import time

import pymongo
from config import DB_CONFIG, MONGO_DB, MONGO_COLL, TOKEN_COLL
from db.ISqlHelper import ISqlHelper


class MongoHelper(ISqlHelper):
    def __init__(self):
        self.client = pymongo.MongoClient(DB_CONFIG['DB_CONNECT_STRING'], connect=False)

    def init_db(self):
        self.db = self.client[MONGO_DB]
        self.coll = self.db[MONGO_COLL]

    def drop_db(self):
        self.client.drop_database(self.db)

    def find_token(self, token):
        if self.db[TOKEN_COLL].find_one({'token': token}):
            return True
        else:
            return False

    def insert_token(self, token):
        if not self.db[TOKEN_COLL].find_one({'token': token}):
            self.db[TOKEN_COLL].insert({'token': token, 'date': time.strftime('%Y-%m-%d %H:%M:%S')})

    def select(self, count=1):
        items = self.coll.find({'is_ok': 0}).limit(count).sort(
            [('last_use_time', pymongo.ASCENDING)])

        results = []
        for item in items:
            self.coll.update_one({'_id': item['_id']}, {'$set': {'last_use_time': time.time()}})
            result = {'ip': item['ip'],
                      'port': item['port'],
                      'uname': item.get('uname', None),
                      'passwd': item.get('passwd', None),
                      }
            results.append(result)
        return results

    def delete(self, ip):
        self.coll.delete_one({'ip': ip})
        return 'ok'


if __name__ == '__main__':
    pass

DB_CONFIG = {

    'DB_CONNECT_TYPE': 'pymongo',  # 'pymongo'sqlalchemy;redis
    'DB_CONNECT_STRING': 'mongodb://127.0.0.1:27017/dianping'
    # 'DB_CONNECT_STRING': 'mongodb://user:piowind2017@58.87.103.159:27017/kugou'

    # 'mongodb://username:password@ip:port/authdb'
    # 'DB_CONNECT_STRING': 'sqlite:///' + os.path.dirname(__file__) + '/data/proxys.db'
    # DB_CONNECT_STRING : 'mysql+mysqldb://root:root@localhost/proxys?charset=utf8'
    # 'DB_CONNECT_TYPE': 'redis',  # 'pymongo'sqlalchemy;redis
    # 'DB_CONNECT_STRING': 'redis://localhost:6379/8',

}

MONGO_DB = 'dianping'
MONGO_COLL = 'proxys'
TOKEN_COLL = 'proxys_token'
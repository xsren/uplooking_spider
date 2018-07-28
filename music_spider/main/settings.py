# coding:utf8
import random

'''
common
'''
openUrlTimeout = 3
noHttpProxySleepTime = 60

http_sleep_time = 0  # random.uniform(0.5,1)

u0_no_task_sleep_time = 60 * 60 * 24
u1_no_task_sleep_time = 60
u2_no_task_sleep_time = 0.5
no_task_sleep_time = 60
'''
server
'''
server_ip = "127.0.0.1"
server_port = 2234

# site_type list
site_list = [
    'yiche',
    'autohome',
    'xcar',
    'pcauto',
]

'''
log
'''
# logs_dir
logs_dir_home = './logs'
tmp_dir_home = './tmp'

'''
email
'''

tcp_login_key = 'kkdg2016'

'''
mongo
'''
count_db_name = "songs"
count_coll_name = "count"
# mongodb
mongo_host = "127.0.0.1"
mongo_port = 27017

mongo_user = "songs_user"
mongo_passwd = "songs2018"
auth_db = "songs"
# mongo_user = "root"
# mongo_passwd = "root"
# auth_db = "admin"


def getMCInstance(isAuth=True, isTxMongo=False):
    if isTxMongo:
        from txmongo import MongoConnection as MongoClient
    else:
        from pymongo import MongoClient
    if isAuth:
        mc = MongoClient(mongo_host, mongo_port)
        mc[auth_db].authenticate(mongo_user, mongo_passwd)
        return mc
    else:
        mc = MongoClient(mongo_host)
        return mc


get_tasks_num_one_time = 1
return_tasks_one_time = 30

# queue size
write_queue_size = 0
html_queue_size = 0
task_queue_size = 0
count_queue_size = 0

proxy_one_time_limit = 3

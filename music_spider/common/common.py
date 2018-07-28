# coding:utf8

# action
PUT_SEED = "put_seed"
GET_SEED = "get_seed"
PUT_TASK = "put_task"
GET_TASK = "get_task"
PUT_DATA = "put_data"
UPDATE_DATA = "update_data"
INSERT_DATA_IF_NOT_EXIST = "insert_data_if_not_exist"
PUT_HTML = "put_html"
GET_USER = "get_user"
PUT_USER = "put_user"
GET_PROXY = "get_proxy"
CHANGE_PROXY_STATUS = "change_proxy_status"
CHANGE_SEED_STATUS = "change_seed_status"
CHANGE_TASK_STATUS = "change_task_status"

HAS_NEW = '0'
NOT_HAS_NEW = '1'

# addr
SERVER = "main_server"

# message_type
REQUEST_MESSAGE = "request_message"
RESPONSE_MESSAGE = "response_message"
ECHO_MESSAGE = "echo_message"

# task status
NOT_CRAWL = 0
CRAWLING = 1
CRAWL_SUCCESS = 2
CRAWL_FAIL = 3
INVALID_TASK = 4

# 统计类型
NEW_TASK = "new_task"
ONE_TASK = "one_task"
ONE_DATA = "one_data"
ONE_HTML = "one_html"

# server response status
OK = 0
FAIL = 1

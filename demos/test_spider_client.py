# coding:utf8
import sys

sys.path.append('../common')
import socket_client
import common
import settings


def main():
    db_name = 'songs'
    coll_name = 'test_test'
    data = [{'url': 111, 'status': common.NOT_CRAWL},
            {'url': 222, 'status': common.NOT_CRAWL},
            {'url': 333, 'status': common.NOT_CRAWL},
            ]
    sc = socket_client.SocketClient(host='127.0.0.1', port=2234, key=settings.tcp_login_key, user_name='aaabbb')

    coll_name = 'angel_people_tasks'
    res = sc.get_task(db_name, coll_name, count=2)
    peoples = res['data']
    print(peoples)

    coll_name = 'angel_people_tasks'
    peoples = [{'url': 111,
                'name': 'aaa',
                'status': common.NOT_CRAWL,
                'last_crawl_time': 0
                }
               ]
    sc.put_task(db_name, coll_name, peoples)

    coll_name = 'angel_companies_tasks'
    companies = [{'url': 222,
                  'name': 'bbb',
                  'status': common.NOT_CRAWL,
                  'last_crawl_time': 0
                  }
                 ]
    sc.put_task(db_name, coll_name, companies)

    peoples = [{'url': 111,
                'name': 'aaa',
                'status': common.CRAWL_SUCCESS,
                'last_crawl_time': 0
                },
               {'url': 222,
                'name': 'bbb',
                'status': common.CRAWL_FAIL,
                'last_crawl_time': 0
                },
               ]
    coll_name = 'angel_companies_tasks'
    sc.change_task_status(db_name, coll_name, peoples)


if __name__ == '__main__':
    main()

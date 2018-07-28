# coding:utf8

from gevent import monkey

monkey.patch_all()

# 系统库
import pdb
import importlib
import gevent
import sys
import traceback
import click
import random
import logging
from gevent.queue import Queue

try:
    from gevent.coros import BoundedSemaphore as lock
except Exception as e:
    from gevent.lock import BoundedSemaphore as lock

# 本地库
sys.path.append('../common')
sys.path.append('../crawlers')
import utils
import settings
from socket_client import SocketClient

log_dict = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR,
            'critical': logging.CRITICAL}


@click.command()
@click.option('-s', '--site-name', help=u'选择爬虫类型 wuba_ershouche|ganji_ershouche|yihce_ershouche')
@click.option('-t', '--task-type', help=u'''任务类型
             0 yiche: 0 init_seed | 1 crawl_index | 2 crawl_detail | 3 crawl_people | 4 crawl_peizhi（新车配置）| 5 crawl_chezhujiage（车主价格） | 6 init_car_brand(初始化汽车品牌) | 7 crawl_car_series (爬取汽车系列)''')
@click.option('-n', '--thread-number', help=u'线程数,默认是1', default=1, type=int)
@click.option('-i', '--server-ip', help=u'main_server的ip，如果没有指定则已settings.py中的为准')
@click.option('-p', '--server-port', help=u'main_server的端口，如果没有指定则已settings.py中的为准', type=int)
@click.option('--proxy-type', help=u'代理类型，no(默认，不使用),http，socks', default='no')
@click.option('--log-level', help=u'日志level，debug|info|warning|error|critical,默认info', default='info')
@click.option('--register', help=u'是否注册', default=False, type=bool)
@click.option('--login', help=u'是否登录', default=False, type=bool)
# @click.option()
@click.pass_context
def main(ctx, **kwargs):
    import pdb
    pdb.set_trace()
    # pdb.set_trace()
    site_name = kwargs['site_name']
    task_type = kwargs['task_type']
    thread_number = kwargs['thread_number']
    server_ip = kwargs['server_ip']
    server_port = kwargs['server_port']
    proxy_type = kwargs['proxy_type']
    log_level = log_dict.get(kwargs['log_level'], logging.INFO)
    register = kwargs['register']
    login = kwargs['login']

    import pdb
    pdb.set_trace()
    if site_name is None or task_type is None:
        click.echo(ctx.get_help())
        sys.exit(-1)

    # 初始化logger
    log_dir = '%s/%s_%s.log' % (settings.logs_dir_home, site_name, task_type)
    logger = utils.initLogger(log_dir, log_level)
    # 开始执行爬虫程序
    mainCrawler = MainCrawler(logger, site_name, task_type, thread_number, server_ip, server_port, proxy_type, register,
                              login)
    import pdb
    pdb.set_trace()
    try:
        mainCrawler.run()
    except:
        traceback.print_exc()
        utils.send_email(traceback.format_exc())


class MainCrawler:
    def __init__(self, logger, site_name, task_type, thread_num, server_ip, server_port, proxy_type, register, login):
        import pdb
        pdb.set_trace()
        self.logger = logger
        self.site_name = site_name
        self.task_type = task_type
        self.thread_num = thread_num
        if server_ip == None or server_port == -1:
            self.server_ip = settings.server_ip
            self.server_port = settings.server_port
        else:
            self.server_ip = server_ip
            self.server_port = server_port
        self.proxy_type = proxy_type
        self.register = register
        self.login = login

        # init socket client
        self.task_queue = Queue(0)  # 返回结果
        if self.proxy_type != "no":
            self.proxy_queue = Queue(0)
        else:
            self.proxy_queue = None
        self.write_queue = Queue()
        self.status_queue = Queue()
        self.lock = lock()

        self.threads = []

        self.name = "%s_%s_%s_%s" % (self.site_name, self.task_type, self.thread_num, random.random())

    def run(self):
        # 引入爬虫模块
        m = importlib.import_module(self.site_name)
        import pdb
        pdb.set_trace()
        seeds = Queue()
        if self.task_type == "spec_crawl_index":
            mc = settings.getMCInstance()
            db = mc['automotor_ershouche']
            if self.site_name == "ganji_ershouche":
                cur = db['%s_city' % self.site_name].find({}, {'url': 1, 'pinyin': 1, "name": 1})
            else:
                cur = db['%s_city' % self.site_name].find({}, {'url': 1, "name": 1})
            for c in cur:
                seeds.put(c)
        import pdb
        pdb.set_trace()
        for x in range(self.thread_num):
            sock = SocketClient(host=self.server_ip,
                                port=self.server_port,
                                key=settings.tcp_login_key,
                                user_name=self.name,
                                logger=self.logger)
            crawler = m.Crawler(x, self.logger, self.task_type, self.proxy_type, sock, seeds, self.register, self.login)
            self.threads.append(gevent.spawn(crawler.run))
        import pdb
        pdb.set_trace()
        gevent.joinall(self.threads)


if __name__ == "__main__":
    main()

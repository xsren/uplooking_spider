# coding:utf8
'''
工具函数
'''

import hashlib
import logging
import logging.handlers
import pdb
import re
import smtplib
import sys
import time
# 邮件相关
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from functools import wraps

# 本地库
sys.path.append('../main')
import settings


# from RedisLoggingHandler import RedisLoggingHandler


def t_diff(level):
    def decorate(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start = time.time()
            result = func(self, *args, **kwargs)
            end = time.time()
            msg = '%s,%s' % (func.__name__, (end - start))
            self.logger.log(level, msg)
            return result

        return wrapper

    return decorate


class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt=None):
        logging.Formatter.__init__(self, fmt=fmt)

    def format(self, record):
        COLORS = {
            'Black': '0;30',
            'Red': '0;31',
            'Green': '0;32',
            'Brown': '0;33',
            'Blue': '0;34',
            'Purple': '0;35',
            'Cyan': '0;36',
            'Light_Gray': '0;37',

            'Dark_Gray': '1;30',
            'Light_Red': '1;31',
            'Light_Green': '1;32',
            'Yellow': '1;33',
            'Light_Blue': '1;34',
            'Light_Purple': '1;35',
            'Light_Cyan': '1;36',
            'White': '1;37',
        }
        COLOR_SEQ = "\033[%sm"
        RESET_SEQ = "\033[0m"

        message = logging.Formatter.format(self, record)

        if record.levelno == logging.DEBUG:
            message = COLOR_SEQ % COLORS['Green'] + message + RESET_SEQ
        elif record.levelno == logging.INFO:
            # message = COLOR_SEQ % COLORS['White'] + message + RESET_SEQ
            pass
        elif record.levelno == logging.WARNING:
            message = COLOR_SEQ % COLORS['Brown'] + message + RESET_SEQ
        elif record.levelno == logging.ERROR:
            message = COLOR_SEQ % COLORS['Red'] + message + RESET_SEQ
        elif record.levelno == logging.CRITICAL:
            message = COLOR_SEQ % COLORS['Purple'] + message + RESET_SEQ
        return message


# 日志初始化函数
def initLogger(log_file_name=None, level=logging.DEBUG):
    # create logger 
    logger = logging.getLogger(log_file_name)
    logger.setLevel(level)
    if log_file_name:
        # create file handler which logs even debug messages
        fh = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=1024 * 1024, backupCount=1)
        fh.setLevel(level)
        # create formatter and add it to the handlers
        color_formatter = ColoredFormatter(fmt='%(asctime)s %(funcName)s[line:%(lineno)d] [%(levelname)s]: %(message)s')
        fh.setFormatter(color_formatter)
        # add the handlers to the logger
        logger.addHandler(fh)

        # create error file handler which logs only error messages
        fh_error = logging.FileHandler(log_file_name + '.ERROR')
        fh_error.setLevel(logging.ERROR)
        # create formatter and add it to the handlers
        color_formatter = ColoredFormatter(fmt='%(asctime)s %(funcName)s[line:%(lineno)d] [%(levelname)s]: %(message)s')
        fh_error.setFormatter(color_formatter)
        # add the handlers to the logger
        logger.addHandler(fh_error)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(level)
    color_formatter = ColoredFormatter(fmt='%(asctime)s %(funcName)s[line:%(lineno)d] [%(levelname)s]: %(message)s')
    ch.setFormatter(color_formatter)
    # add the handlers to the logger
    logger.addHandler(ch)
    return logger


def decodeToUnicode(response, isImg=False):
    '''
    为了统一，尝试将编码改为unicode
    '''

    if not isImg:
        if isinstance(response, str):
            return response

        try:
            response = response.decode('utf8')
        except Exception as e:
            try:
                response = response.decode('gbk')
            except Exception as e:
                try:
                    response = response.decode('gb2312')
                except Exception as e:
                    try:
                        response = response.decode('gb18030')
                    except Exception as e:
                        try:
                            response = response.decode('ISO-8859-1')
                        except Exception as e:
                            pass

        # 去除html中的一些非法字符
        response = remove_control_characters(response)

    return response


# 去除html中的一些非法字符
def remove_control_characters(html):
    def str_to_int(s, default, base=10):
        if int(s, base) < 0x10000:
            return chr(int(s, base))
        return default

    try:
        html = re.sub(r"&#(\d+);?", lambda c: str_to_int(c.group(1), c.group(0)), html)
        html = re.sub(r"&#[xX]([0-9a-fA-F]+);?", lambda c: str_to_int(c.group(1), c.group(0), base=16), html)
        html = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", html)
    except Exception as e:
        pass
    return html


# 转换时间格式, 将01:45:50格式转化为整数秒
def convert_film_date(date):
    ds = date.split(':')
    if len(ds) == 3:
        duration = 60 * 60 * int(ds[0]) + 60 * int(ds[1]) + int(ds[2])
    elif len(ds) == 2:
        duration = 60 * int(ds[0]) + int(ds[1])
    else:
        duration = int(ds[0])
    return duration


# 转换时间格式, 将整数秒转化为01:45:50格式
def convert_seconds_to_format(second):
    h = second / 3600
    second = second % 3600
    m = second / 60
    s = second % 60
    return '%02d:%02d:%02d' % (h, m, s)


# 统一area字段格式
def unify_area_field(field):
    if field in [u'华语', u'内地', u'中国大陆']:
        return u'大陆'
    return field


# 统一language字段格式
def unify_language_field(field):
    if field in [u'普通话']:
        return u'国语'
    return field


# md5加密
def md5(src):
    if isinstance(src,str):
        src = src.encode('utf-8')
    m = hashlib.md5()
    m.update(src)
    return m.hexdigest()


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr(( \
        Header(name, 'utf-8').encode(), \
        addr.encode('utf-8') if isinstance(addr, str) else addr))


# 发送邮件,爬虫可以调用该接口通过邮件通知错误信息
# attach 不为None时，会将attach中的内容命名为tmp.html作为附件发送
def send_email(info, attach=None, subject=u'爬虫崩溃信息'):
    from_addr = "hellomylovehl@163.com"
    password = "helloworld"
    to_addr = "rxsrcj@126.com"
    smtp_server = "smtp.163.com"
    if isinstance(attach, str):
        attach = attach.encode('utf8')

    try:
        if attach is None:
            msg = MIMEText(info, 'plain', 'utf-8')
            msg['From'] = _format_addr(u'爬虫通知 <%s>' % from_addr)
            msg['To'] = _format_addr(u'管理员 <%s>' % to_addr)
            msg['Subject'] = Header(subject, 'utf-8').encode()

        else:
            msg = MIMEMultipart()
            msg['From'] = _format_addr(u'爬虫通知 <%s>' % from_addr)
            msg['To'] = _format_addr(u'管理员 <%s>' % to_addr)
            msg['Subject'] = Header(subject, 'utf-8').encode()

            part = MIMEText(info, 'plain', 'utf-8')
            msg.attach(part)

            part = MIMEApplication(StringIO.StringIO(attach).read())
            part.add_header('Content-Disposition', 'attachment', filename="tmp.html")
            msg.attach(part)
    except Exception as e:
        pdb.set_trace()

    try:
        server = smtplib.SMTP(smtp_server, 25)
        # server.set_debuglevel(1)
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
    except Exception as e:
        print(str(object=e))


# 将抓取的网页存入文件中
def save_response_to_file(response):
    fname = '%s/%s.html' % (settings.tmp_dir_home, md5(response))
    fh = open(fname, 'w')
    fh.write(response)
    fh.close()
    return fname


if __name__ == "__main__":
    initLogger('mylog.log')
    send_email("test", "test!!!")
    pass

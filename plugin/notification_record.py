#!/usr/bin/env python
#coding: utf-8
# --------------------------
# 此脚本未来会废弃
# --------------------------
import json
import sys, os
import logging
import redis
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from optparse import OptionParser
from redis import BlockingConnectionPool

# redis 相关配置
REDIS_HOST = '10.2.161.15'
REDIS_PORT = 6379
REDIS_DB_NUM = 0
REDIS_PASSWORD = 'N6MXWf'

# -------------- 日志存储 ------------------
# 日志存储目录
LOG_PATH = "/tmp"


# 提取参数
def parse_args(argv):
    usage = "usage: %prog -A <appname> -H <host> -N <notifytype> -S <state> -O <output>"
    
    parser = OptionParser(usage=usage)
    
    parser.add_option("-A", "--appname", action="store", type="string", dest="appname", help="appname")
    
    parser.add_option("-H", "--host", action="store", type="string", dest="host", help="host")
    
    parser.add_option("-N", "--notifytype", action="store", type="string", dest="notifytype", help="notify type")
    
    parser.add_option("-S", "--state", action="store", type="string", dest="state", help="state")
    
    parser.add_option("-O", "--output", action="store", type="string", dest="output", help="output")
    
    (options, args) = parser.parse_args(argv)
    
    return  options
    
def notify_write(type, ip, appname, state, output):
    global REDIS_HOST, REDIS_PORT, REDIS_DB_NUM, REDIS_PASSWORD
    pool = BlockingConnectionPool(max_connections=1, timeout=5, socket_timeout=5, \
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_NUM, password=REDIS_PASSWORD)
    redis_db = redis.StrictRedis(connection_pool=pool)
    
    logger = logging.getLogger()
    
    dd = {}
    dd['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # nagios
    dd['host'] = redis_db.hget('ip_host', ip)
    dd['appname'] = appname
    dd['type'] = type
    dd['state'] = state
    dd['information'] = output
    
    message = json.dumps(dd)
    redis_db.rpush('notification', message)
    pool.disconnect()
    
    # 记录日志
    logger.info(u'记录通知信息:%s', message)
    
    
def initlog(logpath, filename, logLevel=logging.INFO):
    logfile = os.path.join(logpath, filename)
    logger = logging.getLogger()
    # 默认 每天24:00会对日志进行归档,最多保留3天的日志
    handler = TimedRotatingFileHandler(logfile, when='midnight', backupCount=3)
    datefmt = "%Y-%m-%d %H:%M:%S"
    format_str = "[%(asctime)s]: %(levelname)s %(message)s"
    formatter = logging.Formatter(format_str, datefmt)
    handler.setFormatter(formatter)
    handler.setLevel(logLevel)
    logger.addHandler(handler)
    logger.setLevel(logLevel)
    return logger
      
def main():
    global LOG_PATH
    logger = initlog(LOG_PATH, 'notification.log')
    logger.info('------------- start -------------')
    dd = parse_args(sys.argv)
    notify_write(dd.notifytype, dd.host, dd.appname, dd.state, dd.output)
    logger.info('------------- stop -------------')

if __name__ == "__main__":
        main()    

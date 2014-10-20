# -*- coding:utf-8 -*-
import logging
import os
from logging.handlers import TimedRotatingFileHandler

def initlog(logpath, filename, logLevel=logging.NOTSET):
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

#!/usr/bin/env python
# *-*coding:utf-8*-*
import json
import os, sys
from logging.handlers import TimedRotatingFileHandler
import logging, socket
import httplib, urllib
from optparse import OptionParser

# -------------- 短信发送 ------------------
# *** 注意短信内容必须是GBK编码 ***
# 短信通道用户名
SMS_USER = "autonavi252"

# 短信通道密码
SMS_PASSWORD = "gVnendiJ"

# 短信服务器
SMS_SERVER = "10.13.35.134"

# 端口
SMS_PORT = 443

# servlet_url 
SERVLET_URL = "/smmp"

# -------------- 日志存储 ------------------
# 日志存储目录
LOG_PATH = "/tmp"


# 提取参数
def parse_args(argv):
    usage = "usage: %prog  -C <contact> -A <appname> -H <host> -N <notifytype> -S <state>"
    
    parser = OptionParser(usage=usage)
    
    parser.add_option("-C", "--contact", action="store", type="string", dest="contact", help="contact")
    
    parser.add_option("-A", "--appname", action="store", type="string", dest="appname", help="appname")
    
    parser.add_option("-H", "--host", action="store", type="string", dest="host", help="host")
    
    parser.add_option("-N", "--notifytype", action="store", type="string", dest="notifytype", help="notify type")
    
    parser.add_option("-S", "--state", action="store", type="string", dest="state", help="state")
    
    (options, args) = parser.parse_args(argv)
    
    return  options

def create_message(notify_type, host, appname, state):
    message = "%s Service Alert: IP: %s / %s is %s" % (notify_type, host, appname, state)
    return message
    

# *****************************
# *** 注意短信内容必须是GBK编码 ***
# *****************************
def sms(contact, content):
    global SMS_USER, SMS_PASSWORD, SMS_SERVER, SMS_PORT, SERVLET_URL
    logger = logging.getLogger()
    dd = {'name':SMS_USER, 'password':SMS_PASSWORD,
        'mobiles':contact, 'content':content.encode('gbk')}
    body = urllib.urlencode(dd)
    headers = {}
    # 打日志需要的参数
    params = 'mobile:' + contact + ' ' + content
    try:
        conn = httplib.HTTPSConnection(SMS_SERVER, SMS_PORT)
        conn.request("POST", SERVLET_URL, body, headers)
        response = conn.getresponse() 
        # 短信通道不稳定，因此需要日志记录
        logger.info(u'发送短信成功.' + params + '\n' + response.read())
        conn.close()
        
    except socket.error, e:
        logger.error(u'发送短信失败.' + params + str(e))
        
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
    logger = initlog(LOG_PATH, 'sms.log')
    logger.info('------------- start -------------')
    dd = parse_args(sys.argv)
    if not dd.contact:
        return
    
    message = create_message(dd.notifytype, dd.host, dd.appname, dd.state)
    sms(dd.contact, message)
    logger.info('send sms to ' + dd.contact + ',message = ' + message)
    logger.info('------------- stop -------------')
    

if __name__ == "__main__":
    main()    

    

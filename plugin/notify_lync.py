#!/usr/bin/env python
#coding: utf-8
import sys, os
import logging
from logging.handlers import TimedRotatingFileHandler
from optparse import OptionParser
from suds import WebFault
from suds.client import Client

# lync_server
LYNC_SERVER = "10.2.145.116"

# -------------- 日志存储 ------------------
# 日志存储目录
LOG_PATH = "/tmp"


# 提取参数
def parse_args(argv):
    usage = "usage: %prog  -E <recipients> -A <appname> -H <host> -N <notifytype> -S <state>"
    
    parser = OptionParser(usage=usage)
    
    # 收件人列表
    help_str = 'email or emiallist'  
    parser.add_option("-E", "--recipients", action="store", type="string", dest="recipients", help=help_str)
    
    parser.add_option("-A", "--appname", action="store", type="string", dest="appname", help="appname")
    
    parser.add_option("-H", "--host", action="store", type="string", dest="host", help="host")
    
    parser.add_option("-N", "--notifytype", action="store", type="string", dest="notifytype", help="notify type")
    
    parser.add_option("-S", "--state", action="store", type="string", dest="state", help="state")
    
    (options, args) = parser.parse_args(argv)
    
    return  options
    

def create_message(notify_type, host, appname, state):
    message = "%s Service Alert: IP: %s / %s is %s" % (notify_type, host, appname, state)
    return message
        
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
    
def lync(contact, content):
    global LYNC_SERVER
    lyncurl = 'http://%s/LyncSendMsgService.asmx?WSDL' % LYNC_SERVER
    client = Client(lyncurl)
    print client
    contactarray=contact.split(",")
    url = client.factory.create('ArrayOfString')
    message = client.factory.create('ArrayOfString')
    for c in contactarray:
        lynccontact='sip:'+c
        url.string = [lynccontact.decode('UTF8')]
        message.string = [content.decode('UTF8')]
        #url.string = ['sip:tao.lus@autonavi.com']
        #message.string = ['testtest']
        client.service.SendLyncMessage(url,message)
      
def main():
    global LOG_PATH
    logger = initlog(LOG_PATH, 'lync.log')
    logger.info('------------- start -------------')
    dd = parse_args(sys.argv)
    if not dd.recipients:
        return
        
    message = create_message(dd.notifytype, dd.host, dd.appname, dd.state)
    lync(dd.recipients, message)
    logger.info('send lync to %s,message = %s', dd.recipients, message)
    logger.info('------------- stop -------------')

if __name__ == "__main__":
        main()    

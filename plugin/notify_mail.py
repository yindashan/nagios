#!/usr/bin/env  python
# *-*coding:utf-8*-*
import os, sys
import smtplib
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from email.mime.text import MIMEText
from optparse import OptionParser

# -------------　邮件发送 --------------------
# smtp 服务器用户名
MAIL_USER = "service02"

# smtp 服务器密码
MAIL_PASSWORD = "Service02"

# 邮件服务器
MAIL_SERVER = "smtp.autonavi.com"


# -------------- 日志存储 ------------------
# 日志存储目录
LOG_PATH = "/tmp"


# 提取参数
def parse_args(argv):
    usage = "usage: %prog  -E <recipients> -A <appname> -H <host> -N <notifytype> -S <state> -I <info>"
    
    parser = OptionParser(usage=usage)
    
    # 收件人列表
    help_str = 'email or emiallist'  
    parser.add_option("-E", "--recipients", action="store", type="string", dest="recipients", help=help_str)
    
    parser.add_option("-A", "--appname", action="store", type="string", dest="appname", help="appname")
    
    parser.add_option("-H", "--host", action="store", type="string", dest="host", help="host")
    
    parser.add_option("-N", "--notifytype", action="store", type="string", dest="notifytype", help="notify type")
    
    parser.add_option("-S", "--state", action="store", type="string", dest="state", help="state")
    
    parser.add_option("-I", "--info", action="store", type="string", dest="info", help="info")
    
    
    (options, args) = parser.parse_args(argv)
    
    return  options

# 发送邮件
# to_addrs --此参数可以是list或着string
def send_mail(from_addr, to_addrs, sub, content):
    global MAIL_USER, MAIL_PASSWORD, MAIL_SERVER
    logger = logging.getLogger()
    msg = MIMEText(content, _subtype='plain', _charset='utf-8')
    msg['Subject'] = sub
    msg['From'] = from_addr
    
    if isinstance(to_addrs, basestring):
        msg['To'] = to_addrs
    else:
        msg['To'] = ';'.join(to_addrs)
        
    agent_from = "<" + MAIL_USER + "@autonavi.com>"
    
    try:
        server = smtplib.SMTP()
        server.connect(MAIL_SERVER)
        server.login(MAIL_USER, MAIL_PASSWORD)
        server.sendmail(agent_from, to_addrs, msg.as_string())
        server.quit()
    except Exception, e:
        logger.error(u'邮件发送失败:' + str(e))
        print u'邮件发送失败:' + str(e)
        
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
        
def gen_subject(notify_type, host, appname, state):
    subject = "***%s Service Alert: IP: %s / %s is %s***" % (notify_type, host, appname, state)
    return subject
    
def gen_content(notify_type, host, appname, state, info):
    ll = []
    ll.append("Notification Type: %s\n" % notify_type)
    ll.append("Service: %s\n" % appname)
    ll.append("Host: %s\n" % host)
    ll.append("State: %s\n" % state)
    curr_time = datetime.now()
    ll.append("Date/Time: %s\n" % curr_time.strftime("%Y-%m-%d %H:%M:%S"))
    ll.append("\n")
    ll.append("Additional Info:\n")
    if info:
        ll.append(info)
    else:
        ll.append("null")

    return ''.join(ll)
        
def main():
    global LOG_PATH
    logger = initlog(LOG_PATH,'mail.log')
    logger.info("------  start running ------")
    # 提取参数
    dd = parse_args(sys.argv)
    if not dd.recipients:
        return
        
    emaillist = dd.recipients.split(',')
    subject = gen_subject(dd.notifytype, dd.host, dd.appname, dd.state)
    content = gen_content(dd.notifytype, dd.host, dd.appname, dd.state, dd.info)
    logger.info(u"邮件主题:%s,收件人:%s", subject, dd.recipients)
    # 发送邮件
    content = content.replace('\\n','\n')
    send_mail(u"技术支持中心--运维监控中心", emaillist, subject, content)
    logger.info("------  stop  ------")

if __name__ == '__main__':
    main()       

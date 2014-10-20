# *-*coding:utf-8*-*

# standard library
import os,sys
import json
import httplib
import socket
import os
import logging
import time
import optparse
import subprocess


# our library
from log_record import initlog


#configure the arguments
def parse_args(args):
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    
    # 状态端口号
    help_str = 'the port of the status server'
    parser.add_option('--port', action="store", type='int', dest="port", help=help_str, default=8022)
    
    # 状态服务器IP
    help_str = 'the ip of the status server'  
    parser.add_option('--filepath', action="store", type="string", dest="ip", help=help_str, default='127.0.0.1')
    
    # nagios 配置文件所在路径
    help_str = 'the configuration file path of nagios'  
    parser.add_option('--configpath', action="store", type="string", dest="configpath", help=help_str, default='/opt/nagios/etc/objects/myconfig')
    
    # 日志文件保存路径
    help_str = 'the path of log file.'
    parser.add_option('--logpath', action="store", type='string', dest="logpath", help=help_str, default='/var/log/nagios')
    
    # nagios安装目录  (利用nagios工具检查nagios 配置文件书写是否错误)
    help_str = 'Installation directory of nagios'
    parser.add_option('--install_path', action="store", type='string', dest="install_path", help=help_str, default='/opt/nagios')
    
    # nagios启动命令所在目录  (重新装载配置文件)
    help_str = 'the directory which nagios start command in'
    parser.add_option('--start_path', action="store", type='string', dest="start_path", help=help_str, default='/etc/init.d')
    
       
    tt = parser.parse_args(args) #(options, args)
    return tt[0]

# 剖析 
def dissect(json):
    # 应用
    app_set = set()
    # 主机--host
    host_set = set()
    # 服务--service
    service_set = set()
    # 报警--alarm 形如 busEngine_34687@qq.com,ttt@qq.com_13571996135,15313311111
    alarm_set = set()
    
    for item in json:
        appName = item["name"]
        ip_list = item["ip_list"]
        email_list = item["email_list"]
        mobile_list = item["mobile_list"]
        check_interval = item["check_interval"]
        max_check_attempts = item["max_check_attempts"]
        notify_interval = item.pop("notify_interval", 60)
        
        app_set.add(appName)
        
        for ip in ip_list:
            host_set.add(ip)
        
        alarm_flag = False
        
        if email_list or mobile_list:
            #need to alarm
            alarm_set.add(appName + '=' + listToStr(email_list) + '=' + listToStr(mobile_list))
            alarm_flag = True
            
        service_str = appName + '=' + listToStr(ip_list) + '=' + str(alarm_flag) + '=' 
        service_str += str(check_interval) + '=' + str(max_check_attempts) + '=' + str(notify_interval)
        
        service_set.add(service_str)
    return app_set, host_set, service_set, alarm_set

# create new host config file
def createHostConf(ip, hostsConfPath):
    filename = ip + "_host.cfg"
    f = open(os.path.join(hostsConfPath,filename), 'w')
    lines = ["define host{\n", "use     linux-server\n", "host_name     " + ip + "\n", "alias     " + ip + "\n", "address    " + ip + "\n", "}\n"]
    f.writelines(lines)
    f.close()
    return filename


# change host group config file 
def changeHostGroupConf(appName, ip_list_str, hostsConfPath):
    filename = appName + "_hostgroup.cfg"
    f = open(os.path.join(hostsConfPath,filename), 'w')
    lines = ["define hostgroup{\n", "hostgroup_name     " + appName + "_hostgroup" + "\n", "alias     " + appName + "_hostgroup" + "\n", "members    " + ip_list_str + "\n", "}\n"]
    f.writelines(lines)
    f.close()
    return filename
    
# change new service config file
def changeServicesConf(appName, servicesConfPath, check_interval, max_check_attempts, contactFlag, notifyInterval):
    filename = appName + "_service.cfg"
    f = open(os.path.join(servicesConfPath, filename), 'w')
    lines = []
    lines.append("define service{\n")
    lines.append("use     local-service\n")
    lines.append("hostgroup_name     " + appName + "_hostgroup" + "\n")
    lines.append("service_description     " + appName + "\n")
    lines.append("check_command    " + "check_app" + "\n")
    lines.append("max_check_attempts    " + max_check_attempts + "\n")
    lines.append("normal_check_interval    " + check_interval + "\n")
    lines.append("retry_check_interval    " + check_interval + "\n")
    lines.append("notification_interval    " + notifyInterval + "\n")
    
    #need to be alarm
    if contactFlag:
        lines.append("contact_groups    " + appName + "_contactgroup" + "\n")
        
    lines.append("}\n")
    f.writelines(lines)
    f.close()
    return filename

# change contact config file
def changeContactConf(appname, email_list_str, mobile_list_str, contactsConfPath):
    filename = appname + "_contact.cfg"
    f = open(os.path.join(contactsConfPath, filename), 'w')
    contact_list = []
    
    contact_list.append(appname)
    ll = []
    ll.append("define contact{\n")
    ll.append("contact_name    %s\n" % (appname))
    ll.append("use   generic-contact\n")
    ll.append("alias    %s\n" % (appname))
    ll.append("email    %s\n" % (email_list_str))
    ll.append("}\n")
    
    appname_sms = appname + '_high'
    contact_list.append(appname_sms)
    ll.append("define contact{\n")
    ll.append("contact_name    %s\n" % (appname_sms))
    ll.append("use   generic-contact-sms\n")
    ll.append("alias    %s\n" % (appname_sms))
    ll.append("pager    %s\n" % (mobile_list_str))
    ll.append("}\n")
    
    ll.append("define contactgroup{\n")
    ll.append("contactgroup_name    %s_contactgroup\n" % (appname))
    ll.append("alias    %s\n" % (appname))
    ll.append("members  %s\n" % (','.join(contact_list)))
    ll.append("}\n\n")
    
    f.writelines(ll)
    f.close()
    return filename
    
#把链表中的数据转换成字符串　例: [1,2,3]  -->  '1,2,3'
def listToStr(slist):
    num = len(slist)
    ids = ''
    for i in range(num):
        if i !=0:
            ids += (',' + str(slist[i]))
        else:
            ids += str(slist[i])
    return ids

# 历史json 字符串
def getHistoryJsonStr(path):
    f = open(os.path.join(path, "conf_backups.txt"), 'rw')
    json_history = f.read()
    f.close()
    return json_history
    
# 保存当前json 字符串
def saveJsonStr(path, data):
    f = open(os.path.join(path, "conf_backups.txt"), 'w')
    f.write(data)
    f.close()
    
# 历史json 字符串    
def getNewJsonStr(serverIp,port):
    logger = logging.getLogger()
    # 修改默认超时设置
    socket.setdefaulttimeout(30)
    conn = httplib.HTTPConnection(serverIp, port)
    try:
        conn.request("GET","/app")
        logger.info('Connection successful!')
    except BaseException:
        logger.critical("Connection failed!")
        sys.exit(1)
    response = conn.getresponse()
    return response.read()
     
# 重新配置
# 可以想到真正起作用的是service配置文件,因此对host和contact配置文件都不做删除操作
# 另外如果下次同名的配置文件出现将会覆盖无效的配置文件，对执行效果没有影响
def configChange(json_new_str,json_history_str,configpath,install_path,start_path):
    logger = logging.getLogger()
    # host path
    host_path = os.path.join(configpath,'hosts')
    # service path
    service_path = os.path.join(configpath,'services')
    # contact path
    contact_path = os.path.join(configpath,'contacts')
    
    try:
        json_new = json.loads(json_new_str)
        json_history = json.loads(json_history_str)
    except BaseException:
        logger.critical("json transform failed!")
        sys.exit(2)
    
    app_new_set, host_new_set, service_new_set, alarm_new_set = dissect(json_new)
    app_history_set, host_history_set, service_history_set, alarm_history_set = dissect(json_history)
    
    # host 
    # 只用增加,无需删除
    for ip in host_new_set - host_history_set:
        createHostConf(ip, host_path)
    
    # service
    # 1)service_change 需要创建或者重写service 配置文件的
    # 由三部分组成 1.新增加的应用　2.过去就存在应用,但是ip列表发生变化 3.过去就存在的应用,ip列表未发生变化，但是报警配置发生变化(原先报警，现在不报警，或者反过来)
    for item in service_new_set - service_history_set:
        #  appname#ip1,ip2,ip3#True
        temp_array = item.split('=')
        appname = temp_array[0]
        
        logger.info('The configuration file of ' + appname +' has changed.')
        
        # 变更　hostgroup
        logger.debug(u"变更应用--%s的 hostgroup ",appname)
        changeHostGroupConf(appname, temp_array[1], host_path)
        # 变更　service
        logger.debug(u"变更应用--%s的 service配置 ",appname)
        changeServicesConf(appname, service_path, temp_array[3], temp_array[4], eval(temp_array[2]), temp_array[5])
        
    # 2)需要删除的
    for appname in app_history_set - app_new_set:
        logger.debug(u"删除应用--%s的 service配置 ",appname)
        filename = appname + "_service.cfg"
        filepath = os.path.join(service_path, filename)
        os.unlink(filepath)
        
        logger.info(appname + ' has been deleted.')
        
    # 报警联系人列表
    for item in (alarm_new_set - alarm_history_set):
        temp_array = item.split('=')
        logger.debug(u"修改应用--%s的 报警联系人信息 ",temp_array[0])
        changeContactConf(temp_array[0], temp_array[1], temp_array[2], contact_path)
        
        logger.info('The contact group of ' + temp_array[0] +' has changed.')
        
    
    command = "%s/bin/nagios -v %s/etc/nagios.cfg" % (install_path, install_path)
    # check configure file
    res = subprocess.call(command, shell=True)
    if res == 0:
        # 1.保存当前当前json 字符串
        saveJsonStr(configpath, json_new_str)
        # 2.重载配置
        subprocess.call(start_path + "/nagios reload", shell=True)
        logger.info("nagios reload ok!")
    else:
        logger.error("The nagios configure file is wrong.")
            
def main():
    # 提取配置参数
    dd = parse_args(sys.argv)
    # 初始化日志记录器
    logger = initlog(dd.logpath, 'autoconf.log', logging.DEBUG)
    logger.info("------  start running ------")
    json_new = getNewJsonStr(dd.ip, dd.port)
    logger.debug(u"获取到最新配置信息:%s", json_new)
    json_history = getHistoryJsonStr(dd.configpath)
    logger.debug(u"获取到历史配置信息:%s", json_history)
    
    # 检查是否发生变更
    if json_new != json_history:
        configChange(json_new, json_history, dd.configpath, dd.install_path, dd.start_path)
        
    logger.info("------  stop  ------")
        

if __name__ == "__main__":
        main()

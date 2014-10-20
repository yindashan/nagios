#!/usr/bin/python
# -*- coding:utf-8 -*-

#####################################
# nagios 被动监控模式--检查插件
# ***注意*** 输出必须是UTF-8
#####################################

import os, sys
import json
import httplib
import getopt
import socket
import re, time
import redis
from urllib import quote
from optparse import OptionParser

def parse_args(argv):
	usage = "usage: %prog  -H <vhost> -N <serviceDesc> " 
	parser = OptionParser(usage=usage) 
	
	# 状态转发服务器 IP
	help_str = 'the ip of status server' 
	parser.add_option("-S", "--statusserver", action="store", type="string", dest="status_server", help=help_str, default="10.2.161.15")
	
	# 状态转发服务器 端口号
	help_str = 'the port of status server' 
	parser.add_option("-P", "--port", action="store", type="int", dest="port", help=help_str, default=8022) 
	
	# 当前正在check的应用所在主机   
	# ***注意必须填写 (由nagios提供)
	help_str = 'the host which the application work in' 
	parser.add_option("-H", "--host", action="store", type="string", dest="host", help=help_str) 
	
	# 当前正在check的应用的名称 
	# ***注意必须填写 (由nagios提供) 
	help_str = 'the name of application' 
	parser.add_option("-N", "--name", action="store", type="string", dest="appname", help=help_str)
	
	tt = parser.parse_args(argv) #(options, args)
	
	if tt[0].host == None or tt[0].appname == None:
		print "UNKNOW - Parameter error"
		sys.exit(3)
		
	return tt[0]
	
# connect to transmit_server and get json
def get_app_status(server_ip, port, app, ip):
	conn = httplib.HTTPConnection(server_ip, port, timeout=10)
	ip = ip.replace('.', '_')
	app = quote(app)
	path = "/monitorip/%s/%s" %  (app, ip)
	try:
		conn.request("GET", path)
	except BaseException:
		print "UNKNOW - Connection failure"
		sys.exit(3)
		
	response = conn.getresponse()
	data = response.read()
	
	if len(data) == 0:
		print "UNKNOW - The string of app status is null"
		sys.exit(3)

	if response.status != 200:
		print "CRITICAL - Request failure.The monitor agent may be down."
		sys.exit(2)
	
	try:
		dd = json.loads(data)
	except BaseException:
		print "UNKNOW - json string format error"
		sys.exit(3)
		
	return dd


def note(mode, value, data, data1, data2):
    res = u"当前值: " + str(value) + " " 
    if mode == 1:
        res += u"阈值: 当前值 小于" + str(data)
    elif mode == 2:
        res +=  u"阈值: 当前值 大于" + str(data)
    elif mode == 3:
        res +=  u"阈值: 当前值 小于" + str(data1) + u" 或者 当前值 大于" + str(data2)
    elif mode == 4:
        res += u"阈值: 当前值 大于等于" + str(data1) + u" 并且 当前值 小于等于" + str(data2)
    return res

# monitor value
def monitor(appname, host_ip, app_status, dd):
	# 是否报警
	warning_flag = False
	critical_flag = False
	
	# 描述信息
	status_info_list = []
	perf_data_list = []
	for item in app_status["monitor"]:
		# get monitor records one by one
		value = item["value"]
		warning = item["warning"]
		critical = item["critical"]
		id = item["id"]	
		desc = item["desc"]	
		
		perf_data_list.append("monitor_id_%s=%s;%s;%s;;" % (id, value, warning, critical))  
		
		wflag, wnote_str = judge(value, warning)
		cflag, cnote_str = judge(value, critical)
		
		if cflag:
			critical_flag = True
			status_info_list.append(u"id%s=%s 错误"  % (id, desc))
			status_info_list.append(cnote_str)
			
		elif wflag:
			warning_flag = True
			status_info_list.append(u"id%s=%s 警告"  % (id, desc))
			status_info_list.append(wnote_str)
	
	perf_data = ' '.join(perf_data_list)
	res = '\n'.join(status_info_list) + ' | ' + perf_data
	
	# ***注意*** 必须输出utf8格式的字符串
	res = res.encode('utf-8')
	
	if critical_flag:
		print 'CRITICAL - ' + res 
		sys.exit(2)
	elif warning_flag:
		print 'WARNING - ' + res 
		sys.exit(1)
	else:
		print 'OK - ' + res 
		sys.exit(0)

##parse the threshold from info
def parse_threshold(threshold_str):
    t = None
    t1 = None
    t2 = None
    #mode1-->10: 
    #mode2-->~:10
    #mode3-->10:20
    #mode4-->@10:20
    pattern_list = ['^([\d|\.]+):$','^~:([\d|\.]+)$','^([\d|\.]+):([\d|\.]+)$','^@([\d|\.]+):([\d|\.]+)$']
    for i in range(4):
        res = re.match(pattern_list[i],threshold_str)
        if res is not None:
            if i==0 or i==1:
                t = res.group(1)
                t = float(t)
            else:
                t1 = res.group(1)
                t1 = float(t1)
                
                t2 = res.group(2)
                t2 = float(t2)
            return (i+1,t,t1,t2)
    return None

# judge the value status
def judge(value, threshold_str):
	status = False
	note_str = None
	mode, data, data1, data2 = parse_threshold(threshold_str)
	
	if mode == 1:
		if value < data:
			status = True
	elif mode == 2:
		if value > data:
			status = True
	elif mode == 3:
		if value < data1 or value > data2: 
			status = True
	elif mode == 4:
		if data1 <= value <= data2:
			status = True
			
	if status:
		note_str = note(mode, value, data, data1, data2)
	return status, note_str

def main():
	# 提取参数
	dd = parse_args(sys.argv)
	# 访问状态转发服务器获取应用运行状态信息
	app_status = get_app_status(dd.status_server, dd.port, dd.appname, dd.host)
	# 监控
	monitor(dd.appname, dd.host, app_status, dd)
	
if __name__ == "__main__":
	main()

# encoding: utf-8
"""
读取系统配置参数
"""

import ConfigParser


def read_dns():
    """
    读取所使用的递归服务器
    :return:
    """
    cf = ConfigParser.ConfigParser()
    cf.read('system.conf')
    dns_server = cf.get("dns", "dns_server_wiseye")
    return dns_server

def read_time():
    cf = ConfigParser.ConfigParser()
    cf.read('system.conf')
    timeout = cf.getint("time", "timeout")
    return timeout
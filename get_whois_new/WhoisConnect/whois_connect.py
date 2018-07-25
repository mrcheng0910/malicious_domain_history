#!/usr/bin/env python
# encoding:utf-8
"""
    whois服务器通信
=====================

version   :   1.0
author    :   @`13
time      :   2017.1.18
"""

import socket

from Setting.static import Static
from WhoisConnect.server_ip import ServerIP

Static().static_value_init()  # 静态值初始化
TIMEOUT = Static.SOCKS_TIMEOUT  # 超时设定
RECONNECT = Static.SOCKS_RECONNECT  # 最大重连数
Proxy_Flag = Static.PROXY_SOCKS_FLAG  # 使用代理标志
_proxy_socks = None

# 获取代理ip
if Proxy_Flag:
    from proxy_socks import ProxySocks

    _proxy_socks = ProxySocks()  # socks代理 获取对象

# server_ip 获取对象
_server_ip = ServerIP()


class GetWhoisInfo:
    """WHOIS 通信类"""

    def __init__(self, domain, whois_srv):
        """处理whois服务器,特殊的请求格式"""
        if whois_srv == "whois.jprs.jp":
            self.request_data = "{d}/e".format(d=domain)  # Suppress Japanese output
        elif domain.endswith(".de") and (whois_srv == "whois.denic.de" or whois_srv == "de.whois-servers.net"):
            self.request_data = "-T dn,ace {d}".format(d=domain)  # regional specific stuff
        elif whois_srv == "whois.verisign-grs.com" or whois_srv == "whois.crsnic.net":
            self.request_data = "={d}".format(d=domain)  # Avoid partial matches
        else:
            self.request_data = domain
        self.whois_srv = whois_srv

    def get(self):
        """多次尝试获取数据"""
        for try_time in range(RECONNECT):  # 最大重连数
            no_socket_error = True
            try:
                data = self.__connect()
            except socket.error as socketerror:
                data = 'Socket Error:' + str(socketerror)
                no_socket_error = False
            if try_time == RECONNECT - 1 or no_socket_error:  # 返回没有错误或者最后一次的结果
                return data

    def __connect(self):
        """核心函数：与whois服务器通信"""
        # whois服务器ip，代理ip
        global _server_ip, _proxy_socks
        host = _server_ip.get_server_ip(self.whois_srv)  # 服务器地址
        host = host if host else self.whois_srv  # 如果ip地址为空则使用服务器地址
        # connect
        response = b''
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((host, 43))
        # 发送查询请求
        s.send(bytes(self.request_data) + b'\r\n')
        # 循环接收数据
        while True:
            d = s.recv(4096)
            response += d
            if not d:
                break
        s.close()
        return response


def __Demo(Domain):
    domain = Domain  # 需要获取的域名
    whois_server = 'whois.afilias-grs.info.'  # 域名对应的whois服务器
    data_result = ''
    try:
        data_result = GetWhoisInfo(domain, whois_server).get()  # 获取
    except Exception as e:
        print e
    # if len(data_result) < 100:
    #     print "data->", data_result


if __name__ == '__main__':
    # Demo
    while 1:
        __Demo("yh888.bz")

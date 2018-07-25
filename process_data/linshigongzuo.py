#encoding:utf-8
import DNS

from ip_location.ip2Region import Ip2Region
searcher = Ip2Region('./ip_location/ip2region.db')  # IP定位

timeout = 3


from data_base import MySQL

SOURCE_CONFIG = {
    'host': '10.245.146.37',
    'port': 3306,
    'user': 'root',
    'passwd': 'platform',
    'db': 'illegal_domains_profile',
    'charset': 'utf8'
}


def fetch_mal_domains():
    """
    获取待查询的域名列表
    """

    db = MySQL(SOURCE_CONFIG)
    sql = 'SELECT domain FROM `domain_locate` WHERE reg_whois_province = "广东"'
    db.query(sql)
    query_domains = db.fetch_all_rows()  # 得到总共的数量
    db.close()
    return query_domains


def ip2region(ip=None):
    """
    得到IP的地理位置和运营商
    :param ip: 待查询IP
    :return
        city: ip所在城市，若城市为空，则为国家
        network_operator: 运营商，可能为空
    """
    if ip == "" or ip is None:
        return dict(
            country="",
            region="",
            city="",
            oper=""
        )

    data = searcher.btreeSearch(ip)
    data = data['region'].split('|')
    return dict(
        country=data[0],
        region=data[2],
        city=data[3],
        oper=data[4]
    )
def handle_domain_rc(ns_name,domain):
    """
    获取指定dns记录的内容和ttl时间，主要为A记录和CNAME记录
    """
    ip, ip_ttl, cname, cname_ttl = [], [], [], []
    req_obj = DNS.Request()
    try:
        answer_obj = req_obj.req(name=domain, qtype=DNS.Type.A, server=ns_name, timeout=timeout)
    except DNS.Error, e:
        # print '1获取A/CNAME异常：', domain, e
        try:
            answer_obj = req_obj.req(name=domain, qtype=DNS.Type.A, server=ns_name, timeout=timeout)
        except DNS.Error, e:
            # print '2获取A/CNAME：', domain, e
            return [], [], [], []

    for i in answer_obj.answers:
        r_data = i['data']
        r_ttl = i['ttl']
        if i['typename'] == 'A':
            ip.append(r_data)
            ip_ttl.append(r_ttl)
            geo = ip2region(r_data)
            if geo['region'] == '广东省':
                print geo['region'],domain
        elif i['typename'] == 'CNAME':
            cname.append(r_data)
            cname_ttl.append(r_ttl)

import random

domain = fetch_mal_domains()
domain = list(domain)
random.shuffle(domain)
for i in domain:
    handle_domain_rc('114.114.114.114',i[0])
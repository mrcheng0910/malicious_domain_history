# encoding:utf-8

"""
获取A、CNAME、NS、MX记录和默认TTL值
注意：所有域名都是www，即主页
作者：mrcheng
时间：2018.7.19

"""

import DNS
import random
import time
import tldextract
from system_parameter import read_dns, read_time
from ip_location.ip2Region import Ip2Region

searcher = Ip2Region('./ip_location/ip2region.db')  # IP定位
timeout = read_time()  # 超时时间
local_dns = read_dns()  # 本地递归服务器

g_cnames, g_cnames_ttl, g_ips, g_ips_ttl,g_ns, g_ns_ttl = [], [], [], [], [], []
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


def obtain_ns_ttl(fqdn_domain, server):
    """
    向服务器server发送ns查询请求，获取域名的ns列表和对应的TTL时间
    :param fqdn_domain: 查询的域名
    :param server: 服务器名称
    :return:
        ns：权威服务器列表
        ns_tll：权威服务器TTL值列表
        True/Flase: 是否有异常
    """

    ns, ns_ttl = [], []
    req_obj = DNS.Request()
    try:
        answer_obj = req_obj.req(name=fqdn_domain, qtype=DNS.Type.NS, server=server, timeout=timeout)
    except DNS.Error, e:
        print '1获取ns异常：', fqdn_domain, e
        try:
            answer_obj = req_obj.req(name=fqdn_domain, qtype=DNS.Type.NS, server=server, timeout=timeout)
        except DNS.Error, e:
            print "2获取ns异常:",fqdn_domain, e
            return [], []

    for i in answer_obj.answers:
        if i['typename'] == 'NS':
            ns.append(i['data'])
            ns_ttl.append(i['ttl'])

    return ns, ns_ttl


def find_domain_zone_ns(fqdn_domain):
    """
    获取域名区域负责的NS列表和负责的区域域名
    """
    domain_len = len(fqdn_domain.split('.'))
    for i in range(0, domain_len):
        ns, _ = obtain_ns_ttl(fqdn_domain, local_dns)
        if ns:
            return ns, fqdn_domain
        else:
            fqdn_domain = extract_main_domain(fqdn_domain)
            domain_tld = tldextract.extract(fqdn_domain)
            if fqdn_domain == domain_tld.suffix:  # 顶级域名后缀，即到达域名最后一级
                return [], fqdn_domain


def handle_domain_rc(ns_name,domain):
    """
    获取指定dns记录的内容和ttl时间，主要为A记录和CNAME记录
    """
    ip, ip_ttl, cname, cname_ttl = [], [], [], []
    req_obj = DNS.Request()
    try:
        answer_obj = req_obj.req(name=domain, qtype=DNS.Type.A, server=ns_name, timeout=timeout)
    except DNS.Error, e:
        print '1获取A/CNAME异常：', domain, e
        try:
            answer_obj = req_obj.req(name=domain, qtype=DNS.Type.A, server=ns_name, timeout=timeout)
        except DNS.Error, e:
            print '2获取A/CNAME：', domain, e
            return [], [], [], []

    for i in answer_obj.answers:
        r_data = i['data']
        r_ttl = i['ttl']
        if i['typename'] == 'A':
            ip.append(r_data)
            ip_ttl.append(r_ttl)
        elif i['typename'] == 'CNAME':
            cname.append(r_data)
            cname_ttl.append(r_ttl)

    return ip, ip_ttl, cname, cname_ttl


def obtain_domain_mx(check_domain,ns_name):
    """获取域名MX记录"""
    mxs = []
    mxs_ttl = []
    req_obj = DNS.Request()
    try:
        answer_obj = req_obj.req(name=check_domain, qtype=DNS.Type.MX, server=ns_name,timeout=timeout)
    except DNS.Error,e:
        print "1异常MX",check_domain, e
        try:
            answer_obj = req_obj.req(name=check_domain, qtype=DNS.Type.MX, server=ns_name, timeout=timeout)
        except DNS.Error, e:
            print "2异常MX", check_domain, e
            return [], []
    for i in answer_obj.answers:
        if i['typename'] == 'MX':
            mxs.append(i['data'][1])
            mxs_ttl.append(i['ttl'])

    return mxs, mxs_ttl


def extract_main_domain(fqdn_domain):
    """
    获取次级域名
    """
    fqdn = fqdn_domain.split('.')
    fqdn.pop(0)
    main_domain = '.'.join(fqdn)
    return main_domain


def fetch_rc_ttl(fqdn_domain):
    """
    递归获取域名的cname、cname_ttl和IP、IP_ttl记录
    """
    ns, ns_fqdn_domain = find_domain_zone_ns(fqdn_domain)  # 得到ns列表
    #  若无ns，则停止
    if not ns:
        g_ns.append([])
        g_ns_ttl.append([])
        return

    ns_name = random.choice(ns)   # 随机选择一个ns服务器
    ns, ns_ttl = obtain_ns_ttl(ns_fqdn_domain, ns_name)

    if not ns:  # 只要ns获取不成功，整条记录就是无
        g_ns.append([])
        g_ns_ttl.append([])
        return

    g_ns.append(ns)
    g_ns_ttl.append(ns_ttl)
    ip, ip_ttl, cname, cname_ttl = handle_domain_rc(ns_name, fqdn_domain)  # 得到cname和cname的ttl

    # 若cname不为空，则递归进行cname的dns记录获取
    if cname:
        g_cnames.extend(cname)
        g_cnames_ttl.extend(cname_ttl)
        fetch_rc_ttl(cname[-1])
    else:
        g_ips.extend(ip)
        g_ips_ttl.extend(ip_ttl)
        return


def manage_rc_ttl(original_domain):
    """
    获取a、cname、ns、mx记录和tt时间
    """
    rc_ttl = {}
    global g_cnames, g_cnames_ttl, g_ips, g_ips_ttl,g_ns,g_ns_ttl
    g_cnames, g_cnames_ttl, g_ips, g_ips_ttl,g_ns, g_ns_ttl = [], [], [], [], [], []  # 初始化
    ips_geo = []
    domain_tld = tldextract.extract(original_domain)
    if domain_tld.suffix == "":  # 域名组成不合法
        return
    else:
        check_domain = domain_tld.domain+'.'+domain_tld.suffix
    fqdn_domain = 'www.' + check_domain  # 组合成www全域名
    # print '查询的域名：', check_domain   # 在查询的域名

    fetch_rc_ttl(fqdn_domain)
    if not g_ns[0]:
        rc_ttl['mxs'],rc_ttl['mxs_ttl'] = [], []
    else:
        ns_name = random.choice(g_ns[0])
        rc_ttl['mxs'], rc_ttl['mxs_ttl'] = obtain_domain_mx(original_domain, ns_name)

    rc_ttl['ns'],rc_ttl['ns_ttl'], rc_ttl['cnames'],rc_ttl['cnames_ttl'],rc_ttl['ips'],rc_ttl['ips_ttl'] = g_ns[0], g_ns_ttl[0], g_cnames, g_cnames_ttl, g_ips, g_ips_ttl
    for ip in g_ips:
        ips_geo.append(ip2region(ip))
    rc_ttl['ips_geo'] = ips_geo
    return rc_ttl


if __name__ == '__main__':

    fp = open('malware_domains.txt','r')
    for check_domain in fp.readlines()[200:220]:
        check_domain = check_domain.split('\t')[0].strip()
        print manage_rc_ttl(check_domain)
    fp.close()
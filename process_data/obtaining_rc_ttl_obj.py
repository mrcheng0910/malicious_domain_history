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
    try:
        data = data['region'].split('|')
    except:
        return dict(
            country="",
            region="",
            city="",
            oper=""
        )

    geo = {}
    try:
        geo['country'] = data[0]
    except:
        geo['country'] = ""
    try:
        geo['region'] = data[2]
    except:
        geo['region'] = ""
    try:
        geo['city'] = data[3]
    except:
        geo['city'] = ""
    try:
        geo['oper'] = data[4]
    except:
        geo['oper'] = ""

    return geo


class DomainRecord(object):
    def __init__(self,original_domain):
        self.original_domain = original_domain   # 原始域名
        self.register_domain,self.www_domain = self.extract_register_domain()  # 注册域名和www域名
        self.g_cnames, self.g_cnames_ttl, self.g_ips, self.g_ips_ttl, self.g_ns, self.g_ns_ttl,self.g_mxs,self.g_mxs_ttl,self.g_ips_geo = [], [], [], [], [], [],[],[],[]
        self.local_dns = read_dns()
        self.recursion_depath = 0   # 出现递归深度出错的异常，设置递归深度

    def extract_register_domain(self):
        """
        提取注册域名和www域名
        """
        domain_tld = tldextract.extract(self.original_domain)
        register_domain = domain_tld.domain + '.' + domain_tld.suffix
        www_domain = 'www.' + register_domain  # 组合成www全域名
        return register_domain, www_domain

    def fetch_rc_ttl(self,fqdn_domain):
        """
        递归获取域名的cname、cname_ttl和IP、IP_ttl记录
        """
        # 控制递归深度，原因为找到，待验证 ，通过检查DNS记录个数超过9
        self.recursion_depath += 1
        if self.recursion_depath > 11:
            return

        ns, ns_fqdn_domain = self.find_domain_zone_ns(fqdn_domain)  # 得到ns列表
        #  若无ns，则停止
        if not ns:
            self.g_ns.append([])
            self.g_ns_ttl.append([])
            return

        ns_name = random.choice(ns)   # 随机选择一个ns服务器
        ns, ns_ttl = self.obtain_ns_ttl(ns_fqdn_domain, ns_name)

        if not ns:  # 只要ns获取不成功，整条记录就是无
            self.g_ns.append([])
            self.g_ns_ttl.append([])
            return

        self.g_ns.append(ns)
        self.g_ns_ttl.append(ns_ttl)
        ip, ip_ttl, cname, cname_ttl = self.handle_domain_rc(ns_name, fqdn_domain)  # 得到cname和cname的ttl

        # 若cname不为空，则递归进行cname的dns记录获取
        if cname:
            self.g_cnames.extend(cname)
            self.g_cnames_ttl.extend(cname_ttl)
            self.fetch_rc_ttl(cname[-1])
        else:
            self.g_ips.extend(ip)
            self.g_ips_ttl.extend(ip_ttl)
            return

    def find_domain_zone_ns(self,fqdn_domain):
        """
        获取域名区域负责的NS列表和负责的区域域名
        """
        domain_len = len(fqdn_domain.split('.'))
        for i in range(0, domain_len):
            ns, _ = self.obtain_ns_ttl(fqdn_domain, self.local_dns)
            if ns:
                return ns, fqdn_domain
            else:
                fqdn_domain = extract_main_domain(fqdn_domain)
                domain_tld = tldextract.extract(fqdn_domain)
                if fqdn_domain == domain_tld.suffix:  # 顶级域名后缀，即到达域名最后一级
                    return [], fqdn_domain

    def return_domain_rc(self):

        rc_ttl = {}
        rc_ttl['ns'], rc_ttl['ns_ttl'], rc_ttl['cnames'], rc_ttl['cnames_ttl'], rc_ttl['ips'], rc_ttl['ips_ttl'], rc_ttl['mxs'], rc_ttl['mxs_ttl'],rc_ttl['ips_geo'] =self.g_ns[0], self.g_ns_ttl[0], self.g_cnames,self.g_cnames_ttl,self.g_ips,self.g_ips_ttl,self.g_mxs,self.g_mxs_ttl,self.g_ips_geo
        return rc_ttl

    def master_control(self):
        self.fetch_rc_ttl(self.www_domain)
        self.obtain_domain_mx()
        self.ip_geo()

    def ip_geo(self):
        for ip in self.g_ips:
            self.g_ips_geo.append(ip2region(ip))

    def obtain_ns_ttl(self,fqdn_domain, server):
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

    def handle_domain_rc(self,ns_name,domain):
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

    def obtain_domain_mx(self):
        """获取域名MX记录"""
        if not self.g_ns[0]:
            self.g_mxs,self.g_mxs_tll = [], []
            return
        ns_name = random.choice(self.g_ns[0])
        req_obj = DNS.Request()
        try:
            answer_obj = req_obj.req(name=self.register_domain, qtype=DNS.Type.MX, server=ns_name,timeout=timeout)
        except DNS.Error,e:
            print "1异常MX",self.register_domain, e
            try:
                answer_obj = req_obj.req(name=self.register_domain, qtype=DNS.Type.MX, server=ns_name, timeout=timeout)
            except DNS.Error, e:
                print "2异常MX", self.register_domain, e
                self.g_mxs, self.g_mxs_tll = [], []
                return
        for i in answer_obj.answers:
            if i['typename'] == 'MX':
                self.g_mxs.append(i['data'][1])
                self.g_mxs_ttl.append(i['ttl'])


def extract_main_domain(fqdn_domain):
    """
    获取次级域名
    """
    fqdn = fqdn_domain.split('.')
    fqdn.pop(0)
    main_domain = '.'.join(fqdn)
    return main_domain


def manage_rc_ttl(original_domain):
    """
    获取a、cname、ns、mx记录和tt时间
    """

    domain_obj = DomainRecord(original_domain)
    domain_obj.master_control()
    return domain_obj.return_domain_rc()


if __name__ == '__main__':
    # manage_rc_ttl('163.com')
    fp = open('malware_domains.txt','r')
    for check_domain in fp.readlines()[200:220]:
        check_domain = check_domain.split('\t')[0].strip()
        manage_rc_ttl(check_domain)
    fp.close()
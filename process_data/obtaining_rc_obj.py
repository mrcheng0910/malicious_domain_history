# encoding:utf-8

"""
获取A、CNAME、NS、MX记录和访问TTL值
注意：所有域名都是www，即主页
作者：mrcheng
时间：2018.7.19

"""

import DNS
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
        self.cnames, self.cnames_ttl, self.ips, self.ips_ttl, self.ns, self.ns_ttl,self.mxs,self.mxs_ttl,self.ips_geo = [], [], [], [], [], [],[],[],[]
        self.local_dns = read_dns()

    def extract_register_domain(self):
        """
        提取注册域名和www域名
        """
        domain_tld = tldextract.extract(self.original_domain)
        register_domain = domain_tld.domain + '.' + domain_tld.suffix
        www_domain = 'www.' + register_domain  # 组合成www全域名
        return register_domain, www_domain

    def fetch_rc_ttl(self):
        """
        递归获取域名的cname、cname_ttl和IP、IP_ttl记录
        """
        # 控制递归深度，原因为找到，待验证 ，通过检查DNS记录个数超过9
        self.obtaining_ns_rc()
        self.obtaining_a_cname_rc()
        self.obtaining_mx_rc()
        self.ip_geo()


    def return_domain_rc(self):

        rc_ttl = {}
        rc_ttl['ns'], rc_ttl['ns_ttl'], rc_ttl['cnames'], rc_ttl['cnames_ttl'], rc_ttl['ips'], rc_ttl['ips_ttl'], rc_ttl['mxs'], rc_ttl['mxs_ttl'],rc_ttl['ips_geo'] =self.ns, self.ns_ttl, self.cnames,self.cnames_ttl,self.ips,self.ips_ttl,self.mxs,self.mxs_ttl,self.ips_geo
        return rc_ttl

    def ip_geo(self):
        for ip in self.ips:
            self.ips_geo.append(ip2region(ip))

    def obtaining_ns_rc(self):
        """
        向服务器server发送ns查询请求，获取域名的ns列表和对应的TTL时间
        :param fqdn_domain: 查询的域名
        :param server: 服务器名称
        :return:
            ns：权威服务器列表
            ns_tll：权威服务器TTL值列表
            True/Flase: 是否有异常
        """

        req_obj = DNS.Request()
        try:
            answer_obj = req_obj.req(name=self.register_domain, qtype=DNS.Type.NS, server=self.local_dns, timeout=timeout)
        except DNS.Error, e:
            print '1获取ns异常：', self.register_domain ,e
            try:
                answer_obj = req_obj.req(name=self.register_domain, qtype=DNS.Type.NS, server=self.local_dns, timeout=timeout)
            except DNS.Error, e:
                print "2获取ns异常:",self.register_domain, e
                return

        for i in answer_obj.answers:
            if i['typename'] == 'NS':
                self.ns.append(i['data'])
                self.ns_ttl.append(i['ttl'])

    def obtaining_a_cname_rc(self):
        """
        获取指定dns记录的内容和ttl时间，主要为A记录和CNAME记录
        """
        req_obj = DNS.Request()
        try:
            answer_obj = req_obj.req(name=self.www_domain, qtype=DNS.Type.A, server=self.local_dns, timeout=timeout)
        except DNS.Error, e:
            print '1获取A/CNAME异常：', self.www_domain, e
            try:
                answer_obj = req_obj.req(name=self.www_domain, qtype=DNS.Type.A, server=self.local_dns, timeout=timeout)
            except DNS.Error, e:
                print '2获取A/CNAME：', self.www_domain, e
                return

        for i in answer_obj.answers:
            r_data = i['data']
            r_ttl = i['ttl']
            if i['typename'] == 'A':
                self.ips.append(r_data)
                self.ips_ttl.append(r_ttl)
            elif i['typename'] == 'CNAME':
                self.cnames.append(r_data)
                self.cnames_ttl.append(r_ttl)

    def obtaining_mx_rc(self):
        """获取域名MX记录"""

        req_obj = DNS.Request()
        try:
            answer_obj = req_obj.req(name=self.register_domain, qtype=DNS.Type.MX, server=self.local_dns,timeout=timeout)
        except DNS.Error,e:
            print "1异常MX",self.register_domain, e
            try:
                answer_obj = req_obj.req(name=self.register_domain, qtype=DNS.Type.MX, server=self.local_dns, timeout=timeout)
            except DNS.Error, e:
                print "2异常MX", self.register_domain, e
                return
        for i in answer_obj.answers:
            if i['typename'] == 'MX':
                self.mxs.append(i['data'][1])
                self.mxs_ttl.append(i['ttl'])


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
    domain_obj.fetch_rc_ttl()
    return domain_obj.return_domain_rc()





if __name__ == '__main__':
    # fp = open('malware_domains.txt','r')
    # for check_domain in fp.readlines()[200:203]:
    #     check_domain = check_domain.split('\t')[0].strip()
    #     print manage_rc_ttl(check_domain)
    # fp.close()
    manage_rc_ttl('1340d.com')
# encoding:utf-8
"""
根据域名名称首字母，解析成该域名存储的表名称
"""


def domain2tb(check_domain):
    """ 根据域名的首字母，选择存储的数据库表名称"""

    if not isinstance(check_domain, str) or len(check_domain) < 1:  # 非字符串和长度小于1的字符串，不符合要求
        # print '异常域名无法转换成表名称：', check_domain
        return False

    first_name = check_domain[0]
    tb_name = ['0jqxyz','16kouv','2efghr','378lnw','459dip','acsmtb']
    for tb in tb_name:
        if first_name in tb:
            return tb+'_history'
    else:
        # print '异常域名无法转换成表名称：',check_domain
        return False

# print domain2tb('gdp8.com')
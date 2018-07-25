# encoding:utf-8
"""
数据库配置文件
"""

# 源数据库配置
SOURCE_CONFIG = {
    'host': '10.245.146.37',
    'port': 3306,
    'user': 'root',
    'passwd': 'platform',
    'db': 'malicious_domain_history',
    'charset': 'utf8'
}

# 目标数据库配置
DESTINATION_CONFIG = {
    'host': '10.245.146.43',
    'port': 3306,
    'user': 'root',
    'passwd': 'platform',
    'db': 'domain_whois_statistics',
    'charset': 'utf8'
}
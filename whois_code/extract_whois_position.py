# encoding:utf-8
"""
提取域名whois信息中的国家、省份、城市、邮编四个字段的信息
"""

import sys
import re

reload(sys)
sys.setdefaultencoding('utf8')


def deal_ZD(src1, src2, src3, details):
    """
    处理字段值
    :param src1: 
    :param src2: 
    :param details: 
    :return: 处理后字段值
    """
    try:
        res = re.search(src1, details).group().strip()
    except:
        try:
            res = re.search(src2, details).group().strip()
        except:
            try:
                res = re.search(src3, details).group().strip()
            except:
                res = ""

    return res


def extract_geo(details):
    """
    从whois的原始信息中提取出注册国家、省份/州、城市、邮编、街道信息
    :param details: 域名whois原始信息
    :return:
        reg_country: 国家
        reg_province: 省份
        reg_city: 城市
        reg_postal: 邮编
        reg_street: 街道
    """
    reg_country = reg_province = reg_city = reg_postal = reg_street = ""

    # 正则匹配语法
    c_reg_country = r'(?<=Registrant Country\:).*(?=\n)'
    c_reg_province = r'(?<=Registrant State/Province\:).*(?=\n)'
    c_reg_city = r'(?<=Registrant City\:).*(?=\n)'
    c_reg_postal = r'(?<=Registrant Postal Code\:).*(?=\n)'
    c_reg_street = r'(?<=Registrant Street.\:).*(?=\n)'

    c_country = r'(?<=Country\:).*(?=\n)'
    c_province = r'(?<=State:).*(?=\n)'
    c_city = r'(?<=City\:).*(?=\n)'
    c_postal = r'(?<=Postal Code\:).*(?=\n)'
    c_street = r'(?<=Street\:).*(?=\n)'

    c_owner_country = r'(?<=owner-country\:).*(?=\n)'
    c_owner_province = r'(?<=owner-state\:).*(?=\n)'
    c_owner_city = r'(?<=owner-city\:).*(?=\n)'
    c_owner_postal = r'(?<=owner-zip\:).*(?=\n)'
    c_owner_street = r'(?<=Registrant Address\:).*(?=\n)'

    if details is not None:
        # reg_province处理
        reg_province = deal_ZD(c_reg_province, c_province,c_owner_province,details)
        # reg_city处理
        reg_city = deal_ZD(c_reg_city,c_city,c_owner_city,details)
        # reg_postal处理
        reg_postal = deal_ZD(c_reg_postal,c_postal,c_owner_postal ,details)
        #reg_country 处理
        reg_country = deal_ZD(c_reg_country, c_country,c_owner_country,details)
        # reg_street 处理
        reg_street = deal_ZD(c_reg_street,c_street,c_owner_street,details)
    #
    # reg_province = mdb.escape_string(reg_province) if reg_province is not None else(reg_province)
    # reg_city = mdb.escape_string(reg_city) if reg_city is not None else(reg_city)
    # reg_postal = mdb.escape_string(reg_postal) if reg_postal is not None else(reg_postal)
    # reg_country = mdb.escape_string(reg_country) if reg_country is not None else(reg_country)

    return reg_country,reg_province,reg_city,reg_postal,reg_street


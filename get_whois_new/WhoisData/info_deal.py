#!/usr/bin/env python
# encoding:utf-8

"""
    whois原始数据处理
=========================

version   :   1.0
author    :   @`13
time      :   2017.2.8
"""

import copy

from whois_func import *  # 提取函数
from Setting.static import Static  # 静态变量,设置
from domain_status import get_status_value  # 处理状态值函数
from domain_time import format_timestamp  # 处理标准时间函数
from WhoisConnect.whois_connect import GetWhoisInfo


Static.log_init()
log_func = Static.LOGGER


def get_result(domain_punycode, tld, whois_addr, func_name, data, flag):
    """
    :param domain_punycode: punycode格式的域名
    :param tld: 顶级域
    :param whois_addr: whois服务器
    :param func_name: 处理函数
    :param data: 服务器返回数据
    :param flag: 数据正确性标记位
    :return: whois 信息字典
    """
    # 返回结果初始化
    domain_whois = {
        "domain": str(domain_punycode),  # 域名
        "tld": tld,  # 顶级域
        "flag": flag,  # 状态标记
        "domain_status": "",  # 域名状态
        "sponsoring_registrar": "",  # 注册商
        "top_whois_server": whois_addr,  # 顶级域名服务器
        "sec_whois_server": "",  # 二级域名服务器
        "reg_name": "",  # 注册姓名
        "reg_phone": "",  # 注册电话
        "standard_phone": "",  # 标准电话
        "phone_country_code": "",  # 电话国家
        "phone_position_code": "",  # 地话地域
        "phone_number": "",  # 纯电话
        "phone_type": 0,  # 电话长度
        "reg_email": "",  # 注册email
        "org_name": "",  # 注册公司名称
        "creation_date": "",  # 创建时间
        "expiration_date": "",  # 到期时间
        "updated_date": "",  # 更新时间
        "details": data,  # 细节
        "name_server": "",  # 域名服务器
    }
    if domain_whois['flag'] < 0:  # ,错误数据直接返回 粗处理结果不调用提取函数
        return domain_whois

    whois_details_first = data
    whois_details_sec = ''
    # 处理原始whois数据
    if func_name == 'com_manage':
        # 针对com,net 等具有二级服务器的域名进行特殊处理
        # 1，处理含有 'xxx='的情况
        whois_details_first = data
        if xxx_bool(whois_details_first):
            whois_details_first = GetWhoisInfo('=' + domain_punycode,
                                               whois_addr).get()
            if whois_details_first.startswith('Socket Error'):
                domain_whois['flag'] = -1  # WHOIS服务器交互过程中出现异常 flag > -1
            elif whois_details_first == '':
                domain_whois['flag'] = -5  # 获取到空数据，flag = -5

        # 2，处理二级whois服务器
        if domain_whois['flag'] < 0:  # 错误数据直接返回 粗处理结果不调用提取函数
            return domain_whois

        whois_server_sec = get_sec_server(whois_details_first,
                                          domain_punycode)
        if whois_server_sec:  # 如果获取到了二级whois地址,更新sec_whois并重新获取数据
            domain_whois['sec_whois_server'] = whois_server_sec
            whois_details_sec = GetWhoisInfo(domain_punycode, whois_server_sec).get()
            if whois_details_sec.startswith('Socket Error') or whois_details_sec.startswith('Your request') or \
                whois_details_sec.startswith('WHOIS LIMIT EXCEEDED') or whois_details_sec.startswith('interval') or\
                whois_details_sec.startswith('IP Address') or whois_details_sec.startswith('ERROR') or \
                whois_details_sec.startswith('You') or whois_details_sec.startswith('The query') or \
                whois_details_sec.startswith('The IP') or whois_details_sec.startswith('We are unable'):
                domain_whois['flag'] = -2  # 二级WHOIS服务器交互过程中出现异常 flag > -2
            elif whois_details_sec == '':
                domain_whois['flag'] = -4  # 二级WHOIS服务器返回空数据，flag > -4
        else:
            domain_whois['flag'] = -3  # 没有获取到二级WHOIS服务器 flag > -3

    # 处理 detail 项中的引号,用于SQL语句 删除多余的 / ' "
    whois_details_first = whois_details_first.replace("\\", "").replace("'", " \\'").replace('"', ' \\"')
    domain_whois['details'] = whois_details_first
    if whois_details_sec:
        whois_details_sec = whois_details_sec.replace("\\", "").replace("'", " \\'").replace('"', ' \\"')
        domain_whois['details'] += "\n##############################\n\n" + \
                                   whois_details_sec

    try:
        # 使用提取函数处理whois获取字典 依次解析一级/二级WHOIS数据
        domain_whois = eval('{func}(whois_details_first, domain_whois)'.format(func=func_name))
        if whois_details_sec:
            sec_domain_whois = copy.deepcopy(domain_whois)  # 这里一定要是深复制,否则会改变原始的内容
            sec_domain_whois = eval('{func}(whois_details_sec, sec_domain_whois)'.format(func=func_name))
            # 合并字典
            for k in sec_domain_whois.keys():  # 只更新部分字段
                if k in ["sponsoring_registrar",
                         "sec_whois_server",
                         "reg_name",
                         "reg_phone",
                         "reg_email",
                         "org_name",
                         "creation_date",
                         "expiration_date",
                         "updated_date",
                         "name_server"]:
                    if sec_domain_whois[k].strip():
                        domain_whois[k] = sec_domain_whois[k]
    except Exception as e:
        log_func.error(domain_punycode + '->' + func_name + ' 提取函数处理失败 ' + str(e))

    # 处理状态值、标准时间、电话
    domain_whois['domain_status'] = get_status_value(domain_whois['domain_status'])
    domain_whois['creation_date'] = format_timestamp(domain_whois['creation_date'])
    domain_whois['expiration_date'] = format_timestamp(domain_whois['expiration_date'])
    domain_whois['updated_date'] = format_timestamp(domain_whois['updated_date'])

    return domain_whois


# 用来判断com_manage函数中，得到的whois信息是否包含xxx标志，若包括则需要重新发送
def xxx_bool(data):
    if data.find('\"xxx\"') != -1 and data.find('\"=xxx\"') != -1:
        return True
    else:
        return False


# 提取com_manage中whois信息中的，二级whois服务器名称
def get_sec_server(data, domain):
    if not data:
        return False
    if data.find("Domain Name: %s" % domain.upper()) != -1:
        pos = data.find("Domain Name: %s" % domain.upper())
        data = data[pos:]
        pattern = re.compile(r"Whois Server:.*|WHOIS Server:.*")
        sec_whois_server = ''
        for match in pattern.findall(data):
            if match.find('Server:') != -1:
                sec_whois_server = match.split(':')[1].strip()
        return False if sec_whois_server == '' else sec_whois_server
    elif data.find('Registrar WHOIS Server:') != -1:  # ws二级服务器
        pattern = re.compile(r'Registrar WHOIS Server:.*?')
        sec_whois_server = ''
        for match in pattern.findall(data):
            if match.find('Server:') != -1:
                sec_whois_server = match.split(':')[1].strip()
        return False if sec_whois_server == '' else sec_whois_server
    else:
        return False

#!/usr/bin/env python
# encoding:utf-8

"""
针对godaddy域名进行修复探测
"""

import sys
reload(sys)
sys.setdefaultencoding('utf8')


import random
from get_whois_new.WhoisData.domain_time import format_timestamp
from get_whois_new.Setting.global_resource import *  # 全局资源
from get_whois_new.Setting.static import Static  # 静态变量,设置
from get_whois_new.WhoisConnect import whois_connect  # Whois通信
# from WhoisConnect import whois_connect_by_socks as whois_connect  # Whois通信
from get_whois_new.WhoisData.info_deal import get_result  # Whois处理函数
from get_whois_new.Database.update_record import WhoisRecord  # 更新信息函数
from get_whois_new.Database.db_opreation import DataBase  # 数据库对象

from whois_code.extract_whois_position import extract_geo
from whois_code.match_province_city import verify_province_city

import time
import threading
from threading import Thread
from Queue import Queue
from datetime import datetime

num_thread = 10      # 线程数量
queue = Queue()     # 任务队列，存储sql
lock = threading.Lock()  # 变量锁

from get_whois_new.data_base import MySQL
from get_whois_new.config import SOURCE_CONFIG

from get_whois_new.phone2geo.phone_locate import get_phone_locate
from get_whois_new.postal2geo.analysis_postal2 import get_postal_locate

Static.init()
Resource.global_object_init()
log_get_whois = Static.LOGGER


def fetch_domain_whois(raw_domain=""):
    """
    获取whois信息和解析出关键字段
    :param raw_domain: 输入域名
    :return: whois信息字典 / 获取失败返回None
    """
    # log_get_whois.info(raw_domain + ' - start')

    # 处理域名信息
    Domain = Resource.Domain(raw_domain)
    domain_punycode = Domain.get_punycode_domain()  # punycode编码域名
    try:
        tld = Domain.get_tld()  # 域名后缀
    except BaseException, e:
        print e
        log_get_whois.error(str(raw_domain) + '域名TLD提取出现错误')
        return None

    WhoisSerAddr = Resource.TLD.get_server_addr(tld)  # 获取whois地址,失败=None
    WhoisSerIP = Resource.WhoisSrv.get_server_ip(WhoisSerAddr)  # 获取whois地址的ip(随机取一个),失败=None
    WhoisFunc = Resource.WhoisFunc.get_whois_func(WhoisSerAddr)  # 获取TLD对应的提取函数名称

    # 获取用于通信的whois服务器地址
    # 优先级 : ip > whois地址 > None (失败)
    WhoisConnectAddr = WhoisSerIP if WhoisSerIP else WhoisSerAddr
    if not WhoisConnectAddr:
        log_get_whois.error(raw_domain + ' | ' + tld + ' - whois通信地址获取失败')
        return None

    # 获取原始whois数据
    raw_whois_data = ''  # 原始whois数据
    data_flag = 1  # whois通信标记
    raw_whois_data = whois_connect.GetWhoisInfo(domain_punycode, WhoisConnectAddr).get()
    if raw_whois_data.startswith('Socket Error'):
        data_flag = -1
    if raw_whois_data == '':
        data_flag = -5  # 获取到空数据，flag = -5

    # 处理原始whois数据
    whois_dict = get_result(domain_punycode,
                            tld,
                            str(WhoisSerAddr),
                            WhoisFunc,
                            raw_whois_data,
                            data_flag)

    # WHOIS信息的地理位置
    whois_geo = {}
    reg_country, reg_province, reg_city, reg_postal, reg_street = extract_geo(whois_dict['details'])
    whois_geo['reg_country'] = reg_country
    whois_geo['reg_province'] = reg_province
    whois_geo['reg_city'] = reg_city
    whois_geo['reg_postal'] = reg_postal
    whois_geo['reg_street'] = reg_street

    return whois_dict, whois_geo


def update_domain_whois_locate(db, whois_dict, whois_geo):
    """
    更新数据库中域名的WHOIS信息和locate信息
    :param db: 数据库
    :param whois_dict: whois信息
    :param whois_geo: 地理信息
    """
    domain, reg_phone, reg_email = whois_dict['domain'], whois_dict['reg_phone'], whois_dict['reg_email']
    org_name = whois_dict['org_name']
    reg_name = whois_dict['reg_name']
    registrar_name = whois_dict['sponsoring_registrar']
    details = whois_dict['details']
    top_srv, ns, flag = whois_dict['top_whois_server'], whois_dict['name_server'], whois_dict['flag']
    reg_date, exp_date, update_date = whois_dict['creation_date'], whois_dict['expiration_date'], whois_dict['updated_date']
    status, tld, sec_srv = whois_dict['domain_status'], whois_dict['tld'].encode('utf8'), whois_dict['sec_whois_server']

    sql_whois = (
        'UPDATE domain_whois set org_name="%s", update_date="%s",reg_phone="%s",reg_email="%s", '
        'expiration_date="%s",reg_name="%s",top_whois_server="%s",name_server="%s",creation_date="%s",'
        'flag="%s",domain_status="%s",details="%s",sponsoring_registrar="%s",tld="%s",sec_whois_server="%s"'
        'WHERE domain="%s" '
    )
    try:
        db.update(sql_whois % ( org_name, update_date, reg_phone, reg_email, exp_date, reg_name, top_srv, ns, reg_date, \
                            flag, status, details, registrar_name, tld, sec_srv, domain )
              )
    except BaseException, e:
        print "更新域名WHOIS信息出错", e
        return

    reg_country, reg_province, reg_city, reg_postal, reg_street, country, province, city = format_whois_geo(whois_geo)
    reg_phone_country, reg_phone_province, reg_phone_city,reg_phone_type = format_phone_geo(reg_phone)
    reg_postal_country, reg_postal_province, reg_postal_city,reg_postal_type = format_postal_geo(reg_postal)

    cmp_flag = cmp_geo(province,reg_phone_province,reg_postal_province)

    sql_locate = (
        'UPDATE domain_locate set province="%s", city="%s",country_code="%s",street="%s",postal_code="%s",'
        'reg_whois_country="%s",reg_whois_province="%s",reg_whois_city="%s",reg_postal_country="%s",'
        'reg_postal_province="%s",reg_postal_city="%s",reg_phone_country="%s",reg_phone_province="%s",'
        'reg_phone_city="%s",cmp_res="%s",reg_phone_type="%s",reg_postal_type="%s",reg_phone ="%s"'
        'WHERE domain="%s" '

    )
    try:
        db.update(sql_locate % (reg_province, reg_city, reg_country, reg_street, reg_postal, country, province, city, \
                     reg_postal_country,reg_postal_province,reg_postal_city,reg_phone_country,reg_phone_province, \
                     reg_phone_city, cmp_flag, reg_phone_type, reg_postal_type,reg_phone,domain))
    except BaseException, e:
        print "更新当前地理位置信息出错", e
        return


def cmp_geo(reg_whois_province,reg_phone_province,reg_postal_province):
    """
    比较WHOIS地理的一致性,得到结果
    :param reg_whois_province:
    :param reg_phone_province:
    :param reg_postal_province:
    """
    provinces = []
    null_count = 0
    if reg_whois_province:
        provinces.append(str(reg_whois_province.strip()))
    else:
        null_count += 1
    if reg_phone_province:
        provinces.append(str(reg_phone_province.strip()))
    else:
        null_count += 1
    if reg_postal_province:
        provinces.append(str(reg_postal_province.strip()))
    else:
        null_count += 1

    if null_count == 3:
        return 1  # 完全不同，都是无法解析的

    provinces_len = len(provinces)
    provinces_set_len = len(set(provinces))

    flag = provinces_len - provinces_set_len + 1

    return flag


def format_whois_geo(whois_geo):
    country = province = city = ""
    # 更新whois地理信息到基础库中
    reg_country = whois_geo['reg_country']
    reg_province = whois_geo['reg_province']
    reg_city = whois_geo['reg_city']
    reg_postal = whois_geo['reg_postal']
    reg_street = whois_geo['reg_street']

    if reg_country.lower() == 'cn' or reg_country.lower() == 'china':
        result = verify_province_city(reg_province, reg_city)
        country = '中国'
        if result:
            province, city = result['confirmed_province'], result['confirmed_city']
    else:
        country, province, city = reg_country, reg_province, reg_city

    return reg_country, reg_province, reg_city, reg_postal,reg_street,country,province,city


def format_phone_geo(phone):
    """
    转移电话的地理信息
    :param phone: 电话
    :return:
        reg_phone_country: 国家
        reg_phone_province: 省份
        reg_phone_city: 城市
    """
    phone_locate = get_phone_locate(phone)
    reg_phone_country = reg_phone_province = reg_phone_city = ""
    reg_phone_type = 0

    if phone_locate['province']:  # 存在省份
        reg_phone_country = '中国'
        reg_phone_province = phone_locate['province']
        reg_phone_city = phone_locate['city']
        reg_phone_type = phone_locate['type']

    return reg_phone_country, reg_phone_province, reg_phone_city,reg_phone_type


def format_postal_geo(postal):
    """
    转译邮编的地理信息
    :param postal: 邮编
    :return:
        reg_postal_country：注册国家
        reg_postal_province: 注册省份
        reg_postal_city: 注册城市
    """
    postal_locate,reg_postal_type = get_postal_locate(postal)  # 得到邮编的中国地理位置
    reg_postal_country = reg_postal_province = reg_postal_city = ""

    if postal_locate[0]:  # 不为None
        reg_postal_country = postal_locate[0]
        reg_postal_province = postal_locate[1]
        reg_postal_city = postal_locate[2]

    return reg_postal_country, reg_postal_province, reg_postal_city,reg_postal_type


def update_whowas(db, domain):
    """
    更新whowas信息，包括whowas表和地理信息表domain_locate
    :param db:
    :param domain:
    """
    # 更新domain_whowas表
    sql = 'insert into domain_whowas (domain,flag,insert_time,tld,domain_status,sponsoring_registrar, \
          top_whois_server,sec_whois_server,reg_name,reg_phone,reg_email,org_name,name_server,creation_date, \
          expiration_date,update_date,details)  select domain,flag,insert_time,tld,domain_status,sponsoring_registrar, \
          top_whois_server,sec_whois_server,reg_name,reg_phone,reg_email,org_name,name_server,creation_date,expiration_date, \
          update_date,details from domain_whois WHERE domain = "%s"'
    try:
        db.update(sql % domain)
    except BaseException,e:
        print e
        return


    # 更新domain_locate_was表
    sql = 'insert into domain_locate_was (domain,reg_whois_country,reg_whois_province,reg_whois_city,reg_whois_street, \
          reg_postal_country,reg_postal_province,reg_postal_city,reg_phone_country,reg_phone_province,reg_phone_city, \
          province,country_code,city,street,postal_code,reg_phone,cmp_res,insert_time,reg_postal_type, \
          reg_phone_type,reg_whois_type)  select domain,reg_whois_country,reg_whois_province,reg_whois_city,reg_whois_street, \
          reg_postal_country,reg_postal_province,reg_postal_city,reg_phone_country,reg_phone_province,reg_phone_city,province, \
          country_code,city,street,postal_code,reg_phone,cmp_res,insert_time,reg_postal_type,reg_phone_type, \
          reg_whois_type from domain_locate WHERE domain = "%s" '
    try:
        db.update(sql % domain)
    except BaseException, e:
        print e
        return


def update_domain_info(whois_dict, whois_geo, rule):
    """
    依据更新规则，更新信息到数据库表中
    """
    domain = whois_dict['domain']
    db = MySQL(SOURCE_CONFIG)
    if 1 in rule:
        print domain + ' ,' + str(rule)+str(datetime.now())
    # 注意更新顺序，先更新WHOWAS表
    if rule[1]:  # 是否更新WHOWAS表
        update_whowas(db, domain)

    if rule[0]:  # 是否更新WHOIS表
        update_domain_whois_locate(db, whois_dict, whois_geo)

    db.close()


def update_domain_whois():
    """
    更新域名的WHOIS信息
    """
    while 1:

        domain, update_date, expiration_date, details, tld, origin_flag = queue.get()  # 从队列中读出域名信息
        print queue.qsize()   # 剩余的域名数量
        try:
            whois_dict, whois_geo = fetch_domain_whois(domain)
        except BaseException, e:
            print domain, '获取WHOIS和解析WHOIS异常', e
            queue.task_done()  # 任务完成
            time.sleep(1)
            continue
        # lock.acquire()  # 锁
        # 依据更新规则，更新数据库中的域名WHOIS相关信息
        try:
            rule = update_rule(whois_dict, update_date, expiration_date, details, tld,origin_flag)
            update_domain_info(whois_dict, whois_geo, rule)
        except BaseException, e:
            print "异常",e
            pass
        # lock.release()  # 解锁
        queue.task_done()
        time.sleep(1)  # 去掉偶尔会出现错误


def update_rule(whois_dict, origin_update_date, origin_expiration_date, details, tld,origin_flag):
    """
    更新数据库的规则判断，主要包括以下规则：
    1. 首次探测，即details为空，需要更新WHOIS数据库表，WHOWAS不需要
    2. 非首次探测，但原域名不存在，判断依据是update_date和expiartion_date相同
        2.1 当前探测的域名依然不存在，不更新WHOIS和WHOWAS数据库
        2.2 当前探测后，域名已经存在，原数据加入到WHOWAS中，当前探测结果存入WHOIS表中
    3. 非首次探测，原域名存在有信息。判断当前探测结果中的update_date与原信息中的update_date是否一致
        3.1 一致则表示未改变，不修改结果
        3.2 不一致，表示有更新，修改WHOIS中数据，将原数据更新如WHOWAS中
    4. 获取WHOIS信息出现异常，则不更新
    5. 原信息完整而最新数据不完整，则不更新
    注意：
    1. 统一转换时间格式
    """

    # [0/1,0/1],表示是否更新WHOIS和WHOWAS表
    rules = {
        'first_detect':  [1, 0],
        'still_not_exist': [0, 0],
        'not_exist_change': [1, 1],
        'not_change': [0, 0],
        'change': [1, 1]

    }
    not_update_flags = [-3, -1, -5]  # 出现这几个标记的话，不更新域名
    flag = whois_dict['flag']  # 获取信息的内容

    if not details:
        return rules['first_detect']

    origin_update_date = format_timestamp(origin_update_date)
    origin_expiration_date = format_timestamp(origin_expiration_date)
    update_date = format_timestamp(whois_dict['updated_date'])
    expiration_date = format_timestamp(whois_dict['expiration_date'])


    if flag in not_update_flags:    # 出现异常flag，不更新
        return rules['not_change']


    if origin_flag == 1 and flag == -2:  # 原始信息完整，最新不完整，不更新
        return rules['not_change']

    if tld == 'cn':
        if details == whois_dict['details']:
            return rules['not_change']
        else:
            return rules['change']

    if origin_update_date == origin_expiration_date:   # 原来不存在的域名
        if update_date == expiration_date:
            return rules['still_not_exist']
        else:
            return rules['not_exist_change']
    else:
        if update_date == origin_update_date:
            return rules['not_change']
        else:
            return rules['change']


def fetch_resource_data():
    """
    获得待查询whois信息的域名，包括域名名称、更新时间、到期时间和详细信息,顶级域名

    注意：
    domain_whois表中的域名是由domain_index中根据触发器更新的
    """
    db = MySQL(SOURCE_CONFIG)
    sql = 'SELECT domain,update_date,expiration_date,LENGTH (details),tld,flag FROM domain_whois WHERE sec_whois_server ="whois.godaddy.com" AND reg_email = "" AND reg_phone = ""'
    db.query(sql)
    query_domains = db.fetch_all_rows()  # 得到总共的数量
    db.close()
    return query_domains


def create_queue():
    """
    创建任务队列
    """
    query_domains = fetch_resource_data()
    query_domains = list(query_domains)
    random.shuffle(query_domains)  # 随机域名
    for d in query_domains:
        queue.put(d)  # num 加入队列


def create_thread():
    """创建任务线程"""
    for q in range(num_thread):  # 开始任务
        worker = Thread(target=update_domain_whois)
        worker.setDaemon(True)
        worker.start()
    queue.join()


def domain_whois():
    """主操作"""
    print str(datetime.now()), '开始获取域名的WHOIS信息'
    create_queue()
    create_thread()
    print str(datetime.now()), '结束获取域名的WHOIS信息'


if __name__ == '__main__':
    domain_whois()
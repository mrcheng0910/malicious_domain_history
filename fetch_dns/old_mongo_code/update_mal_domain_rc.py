# encoding:utf-8

"""
用来获取非法域名无dns记录，但是可以访问的特殊情况

mrcheng
创建：2018.7.27
"""

from db_base import get_col
from datetime import datetime
from obtaining_rc_obj import manage_rc_ttl

import time
import random
from Queue import Queue
from threading import Thread

num_thread = 10  # 线程数量
queue = Queue()  # 任务队列，存储sql
# lock = threading.Lock()
target_col = 'domain_rc_no_ns'
source_col = 'domain_rc'


def fetch_mal_domains():
    """
    获取待查询的域名列表
    """
    domains = []
    try:
        col = get_col(source_col)
        domain_data = col.find({'dns_rc':{'$size':1},'dns_rc.ns':{'$size':0}}, {'domain': 1,'_id':0,'malicious_type':1})  # 得到数据库中已存的记录信息
    except:
        print "pymongo connect error"
        return

    for i in domain_data:
        domains.append((i['domain'],i['malicious_type']))

    return domains


def is_same(source_data1, target_data1):
    """
    判断两个列表是否相同
    """
    return sorted(source_data1) == sorted(target_data1)


def nonexistent_insert_db(check_domain,rc_ttl,mal_type):
    """
    该域名若不存在则插入
    """
    insert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        col = get_col(target_col)
    except:
        print "pymongo connect error"
        return False

    # 域名记录若不存在则插入，存在则不做任何操作
    try:
        result = col.update(
            {
                "domain": check_domain,
             },
            {
                "$setOnInsert":
                 {
                    "dns_rc":
                    [
                        {
                            "cnames": rc_ttl['cnames'],
                            "cnames_ttl": rc_ttl['cnames_ttl'],
                            "ips": rc_ttl['ips'],
                            "ips_geo": rc_ttl['ips_geo'],
                            "ips_ttl": rc_ttl['ips_ttl'],
                            "ns": rc_ttl['ns'],
                            "ns_ttl": rc_ttl['ns_ttl'],
                            "mxs": rc_ttl['mxs'],
                            "mxs_ttl": rc_ttl['mxs_ttl'],
                            "insert_time": insert_time,
                            "last_updated": insert_time
                        }
                    ],
                     "record_time": insert_time,    # 文档插入时间
                     "visit_times": 1,   # 访问次数，初始为1
                     "malicious_type": mal_type  # 恶意类型
                  },
             },
            True
        )
    except:
        print check_domain,"pymongo errors"
        return False

    return result['updatedExisting']   # 是否更新返回标记位，true表示已存在，false表示不存在


def update_time(col, domain, insert_time,cur_time):
    """
    当与最近一条记录相同时，则只更新时间即可
    """
    try:
        col.update(
            {'domain': domain,
             'dns_rc.insert_time': insert_time
             },
            {
                '$set':
                    {'dns_rc.$.last_updated': cur_time},  # 注意$的使用

                "$inc":
                    {
                        "visit_times": 1   # 每次访问增加1
                    }
            }
        )
    except:
        print domain,"pymongo errors"
        pass


def update_data(check_domain, rc_ttl):
    """
    若该条记录存在，则检查该条记录是否需要进行更新
    """
    cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ips, ips_ttl,ips_geo = rc_ttl['ips'],rc_ttl['ips_ttl'],rc_ttl['ips_geo']
    cnames, cnames_ttl = rc_ttl['cnames'], rc_ttl['cnames_ttl']
    ns, ns_ttl = rc_ttl['ns'], rc_ttl['ns_ttl']
    mxs, mxs_ttl = rc_ttl['mxs'], rc_ttl['mxs_ttl']
    try:
        col = get_col(target_col)
    except:
        print "pymongo connect error"
        return
    domain_data = col.find({'domain': check_domain},{'dns_rc': 1})  # 得到数据库中已存的记录信息
    # 得到最新一条的记录
    domain_dns_rc = domain_data[0]['dns_rc'][-1]
    original_ips, original_ips_ttl = domain_dns_rc['ips'], domain_dns_rc['ips_ttl']
    original_cnames, original_cnames_ttl = domain_dns_rc['cnames'], domain_dns_rc['cnames_ttl']
    original_ns, original_ns_ttl = domain_dns_rc['ns'], domain_dns_rc['ns_ttl']
    original_mxs, original_mxs_ttl = domain_dns_rc['mxs'], domain_dns_rc['mxs_ttl']
    original_insert_time = domain_dns_rc['insert_time']

    # 判断IP和TTL是否相同

    if is_same(ips, original_ips) and is_same(cnames,original_cnames) \
            and is_same(ns,original_ns) and is_same(mxs,original_mxs):
        print "记录全部一致，仅更新时间"
        update_time(col, check_domain, original_insert_time, cur_time)
    else:
        print "记录不一致，添加新记录"
        insert_record(col,check_domain, cur_time, rc_ttl)


def insert_record(col, domain, cur_time, rc_ttl):

    name_field = {
        "dns_rc": {
                "cnames": rc_ttl['cnames'],
                "cnames_ttl": rc_ttl['cnames_ttl'],
                "ips": rc_ttl['ips'],
                "ips_geo": rc_ttl['ips_geo'],
                "ips_ttl": rc_ttl['ips_ttl'],
                "ns": rc_ttl['ns'],
                "ns_ttl": rc_ttl['ns_ttl'],
                "mxs": rc_ttl['mxs'],
                "mxs_ttl": rc_ttl['mxs_ttl'],
                "insert_time": cur_time,
                "last_updated": cur_time
        }
    }
    try:
        col.update(
            {'domain': domain},
            {"$push": name_field,
             "$inc":
                 {
                     "visit_times": 1
                 }
             }
        )
    except:
        print domain, "pymongo errors"
        pass


def create_queue():
    """创建队列"""

    domains = fetch_mal_domains()  # 得到要查询的列表
    random.shuffle(domains)
    for check_domain, mal_type in domains:
        queue.put((check_domain, mal_type))


def master_control():
    while 1:

        check_domain, mal_type = queue.get()
        print "查询的域名：", queue.qsize(), check_domain, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rc_ttl = manage_rc_ttl(check_domain)
        insert_flag = nonexistent_insert_db(check_domain, rc_ttl, mal_type)
        if insert_flag:
            update_data(check_domain, rc_ttl)
        else:
            print "域名新插入"
        # lock.acquire()
        # lock.release()  # 解锁
        queue.task_done()
        time.sleep(1)  # 去掉偶尔会出现错误


def main():
    """
    主函数
    """
    print str(datetime.now()), '开始域名DNS记录解析'
    create_queue()
    for q in range(num_thread):  # 开始任务
        worker = Thread(target=master_control)
        worker.setDaemon(True)
        worker.start()
    queue.join()
    print str(datetime.now()), '结束域名DNS记录解析'


if __name__ == '__main__':
    # main()
    while True:
        main()
        time.sleep(600)
    # schedule.every(2).hours.do(main)  # 12小时循环探测一遍
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
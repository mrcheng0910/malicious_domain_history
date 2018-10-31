# encoding:utf-8

"""
1. 获取域名的IP地址以及地理位置，同时更新数据库，更新数据库规则如下：
    1）若数据库中无该域名记录，则插入；
    2）若数据库中有该域名记录，则与该域名最近一次的更新记录进行比较，若相同则不更新，不同则更新。
2. 获取域名的CNAME，同时更新数据库，规则与上相同
3. 获取ns
4. 获取mx

mrcheng
创建：2018.7.19
"""
import sys
reload(sys) # Python2.5 初始化后会删除 sys.setdefaultencoding 这个方法，我们需要重新载入
sys.setdefaultencoding('utf-8')
from datetime import datetime
from obtaining_dns import manage_rc_ttl
import threading
import time
import random
from Queue import Queue
from threading import Thread
from data_base import MySQL
from mysql_config import SOURCE_CONFIG
num_thread = 10  # 线程数量
queue = Queue()  # 任务队列


def fetch_mal_domains():
    """获取待查询的域名列表"""
    db = MySQL(SOURCE_CONFIG)
    sql = 'SELECT domain,visit_times FROM domain_records'
    db.query(sql)
    query_domains = db.fetch_all_rows()  # 得到总共的数量
    db.close()
    return query_domains


def is_same(source_data, target_data):
    """判断两值是否完全相同"""
    return sorted(source_data) == sorted(target_data)


def domain2tb(check_domain):
    """ 根据域名的首字母，选择存储的数据库表名称"""
    first_name = check_domain[0]
    tb_name = ['0jqxyz','16kouv','2efghr','378lnw','459dip','acsmtb']
    for tb in tb_name:
        if first_name in tb:
            return tb+'_history'


def insert_rc_db(check_domain, rc_ttl):
    """
    将探测得到的数据插入到数据库中
    """
    insert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = MySQL(SOURCE_CONFIG)
    tb_name = domain2tb(check_domain)

    first_sql = 'insert into ' + tb_name + '(domain, insert_time, last_updated, ips, ips_ttl, ips_geo, cnames, cnames_ttl, ns, ns_ttl)'
    last_sql = ' VALUES ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")'
    sql = first_sql + last_sql

    # 解析关键字段信息
    ips, ips_geo = rc_ttl['ips'],rc_ttl['ips_geo']
    cnames, ns  = rc_ttl['cnames'], rc_ttl['ns']
    ips_ttl = rc_ttl['ips_ttl'] # 使用map是将数字转换为字符串
    cnames_ttl, ns_ttl = rc_ttl['cnames_ttl'], rc_ttl['ns_ttl']
    last_updated = insert_time

    # 数据插入数据库
    result = db.insert(sql % (check_domain, insert_time, last_updated, ips, ips_ttl, ips_geo, cnames, cnames_ttl, ns, ns_ttl))
    if result == 0:  # 若插入成功，则探测次数加1
        sql = 'update domain_records set visit_times=visit_times+1 where domain = "%s"'
        db.update(sql % check_domain)


def update_time(db, tb_name,domain, last_updated,cur_time):
    """当与最近一条记录相同时，则只更新last_updated时间即可"""

    sql = 'update ' + tb_name + ' set last_updated = "%s" where domain= "%s" and last_updated = "%s"'
    result = db.update(sql%(str(cur_time), domain, last_updated))
    if result:  # 若插入成功，则探测次数加1
        sql = 'update domain_records set visit_times=visit_times+1 where domain = "%s"'
        db.update(sql % domain)


def update_data(check_domain, rc_ttl):
    """若该条记录存在，则检查该条记录是否需要进行更新"""
    cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 最新探测的记录
    ips, cnames, ns = rc_ttl['ips'], rc_ttl['cnames'], rc_ttl['ns']

    # 数据库中存储的最近记录
    db = MySQL(SOURCE_CONFIG)
    tb_name = domain2tb(check_domain)
    sql = 'SELECT ips,cnames,ns,last_updated FROM '+ tb_name + ' WHERE domain="%s" ORDER BY last_updated DESC LIMIT 1'
    db.query(sql % check_domain)
    try:
        original_rc = db.fetch_all_rows()[0]  # 得到总共的数量
        original_ips, original_cnames, original_ns, original_last_updated = original_rc[0], original_rc[1], original_rc[2], original_rc[3]
    except IndexError:
        # original_ips=original_cnames=original_ns=original_last_updated = ""
        insert_rc_db(check_domain, rc_ttl)  # 找不到的话，则插入
        db.close()
        return

    # 判断IP、cname,ns,mx是否变更
    if is_same(ips, original_ips) and is_same(cnames,original_cnames) and is_same(ns,original_ns) :
        # print "记录全部一致，仅更新时间"
        update_time(db, tb_name,check_domain, original_last_updated, cur_time)
        db.close()
    else:
        # print "记录不一致，添加新记录"
        insert_rc_db(check_domain,rc_ttl)
        db.close()


def create_queue():
    """创建任务队列"""
    domains = fetch_mal_domains()  # 得到要查询的列表
    domains = list(domains)
    random.shuffle(domains)
    for check_domain, visit_times in domains:
        queue.put((check_domain,visit_times))


def rc2str(rc_ttl):
    """将域名记录列表转换为字符串形式"""
    for k in rc_ttl:
        try:
            rc_ttl[k] = ','.join(rc_ttl[k])   # 列表内容为字符串
        except:
            rc_ttl[k] = ','.join(map(str,rc_ttl[k]))  # 列表内容为数值

    return rc_ttl


def master_control():
    """主线程控制"""
    while queue.qsize():  # 重要，以前为1，导致线程不结束
        check_domain,visit_times = queue.get()
        # print '活着的线程：', threading.activeCount()
        print queue.qsize(), "查询的域名：", check_domain, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rc_ttl = manage_rc_ttl(check_domain)
        rc_ttl = rc2str(rc_ttl)  # 转换为字符串
        if visit_times == 0:   # 第一次探测域名直接插入到数据库中
            insert_rc_db(check_domain, rc_ttl)
        else:
            update_data(check_domain, rc_ttl)
        queue.task_done()
        # time.sleep(1)  # 去掉偶尔会出现错误


def main():
    """主函数"""
    print str(datetime.now()), '开始解析域名DNS记录'
    create_queue()
    for q in range(num_thread):  # 开始任务
        worker = Thread(target=master_control)
        worker.setDaemon(True)
        worker.start()
    queue.join()
    print str(datetime.now()), '结束解析域名DNS记录'


if __name__ == '__main__':
    while True:
        main()
        time.sleep(600)

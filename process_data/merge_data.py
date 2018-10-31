# encoding:utf-8
from data_base import MySQL
from mysql_config import SOURCE_CONFIG

"""
1. 不能删除域名的最近一条记录，因为新记录需要跟该记录进行对比
    1）获取某域名的last_updated时间最最大值
    2）删除除最大值外的其他last_updated=insert_time情况 
"""


def delete_empty_rc(domain):
    """
    删除空白记录
    """
    db = MySQL(SOURCE_CONFIG)
    # 获取最近一条记录时间
    max_time_sql = 'select max(last_updated) from domain_dns_history WHERE domain= "%s" '
    db.query(max_time_sql % domain)
    max_time = db.fetch_all_rows()[0][0]  # 得到最大值

    # 删除某次探测为空的数据，但不删除最后一条记录
    delete_sql = 'DELETE FROM domain_dns_history WHERE (last_updated = insert_time) AND ips = "" AND domain="%s"  AND last_updated != "%s"'
    db.update(delete_sql % (domain, str(max_time)))
    db.close()


def merge_same_rc(domain):
    """
    最简单的合并相同的记录
    todo:
    1. 以某时间窗口来进行合并，去掉因为探测导致的问题
    """
    domain_rc = []
    rc_last_updated = []
    db = MySQL(SOURCE_CONFIG)

    sql = 'select ips, cnames, ns,last_updated from domain_dns_history WHERE domain="%s"'
    db.query(sql % domain)
    rc = db.fetch_all_rows()

    # 域名记录预处理
    for i in rc:
        domain_rc.append([i[0],i[1],i[2]])
        rc_last_updated.append(str(i[3]))

    # 遍历修改记录
    for i in range(0,len(domain_rc)-1):
        if sorted(domain_rc[i][0]) == sorted(domain_rc[i+1][0]) and sorted(domain_rc[i][1])==sorted(domain_rc[i+1][1]) \
                and sorted(domain_rc[i][2])==sorted(domain_rc[i+1][2]):  # 前后两次的记录是否一致
            ##  若相邻一致的话
            # 先删除后者记录
            delete_sql = 'delete from domain_dns_history WHERE domain="%s" and last_updated="%s"'
            db.update(delete_sql%(domain,rc_last_updated[i+1]))
            # 再将前者记录的last_updated时间修改为后者记录的时间
            update_sql = 'update domain_dns_history set last_updated="%s" WHERE domain="%s" AND last_updated="%s"'
            db.update(update_sql % (rc_last_updated[i+1],domain,rc_last_updated[i]))
        else:
            pass

    db.close()


if __name__ == '__main__':
    domain = '041220.com'
    delete_empty_rc(domain)
    merge_same_rc(domain)
# encoding:utf-8
"""
将mongodb中的数据迁移到mysql中
"""
from data_base import MySQL
from mysql_config import SOURCE_CONFIG
from db_base import get_col
source_col = 'domain_rc'

def fetch_mal_domains():
    try:
        col = get_col(source_col)
        domain_data = col.find()  # 得到数据库中已存的记录信息
    except:
        print "pymongo connect error"
        return

    return domain_data


def insert_index_domains():
    domain_data = fetch_mal_domains()
    db = MySQL(SOURCE_CONFIG)

    for i in domain_data:
        domain = i['domain']
        record_time = i['record_time']
        visit_times = i['visit_times']
        mal_type = i['malicious_type']
        sql = 'insert into domain_records (domain,record_time,visit_times,mal_type) VALUES ("%s","%s","%s","%s")'
        db.update(sql % (domain,record_time,visit_times,mal_type))

def insert_domains_history():
    domain_data = fetch_mal_domains()
    db = MySQL(SOURCE_CONFIG)
    count = 0
    for i in domain_data:
        domain = i['domain']
        dns_rc = i['dns_rc']
        count += 1
        for r in dns_rc:

            insert_time = r['insert_time']
            last_updated = r['last_updated']
            ips = ','.join(r['ips'])
            ips_ttl = ','.join(map(str, r['ips_ttl']))
            ips_geo = []

            for g in r['ips_geo']:
                country = str(g['country'])
                oper = str(g['oper'])
                region = str(g['region'])
                city = str(g['city'])
                geo = country+'|'+region+'|'+city+'|'+oper
                ips_geo.append(geo)

            ips_geo = ','.join(ips_geo)

            cnames = ','.join(r['cnames'])
            cnames_ttl = ','.join(map(str,r['cnames_ttl']))
            ns = ','.join(r['ns'])
            ns_ttl = ','.join(map(str,r['ns_ttl']))
            tb_name = domain2tb(domain)
            first_sql = 'insert into '+ tb_name +' (domain,insert_time,last_updated,ips,ips_ttl,ips_geo,cnames,cnames_ttl,ns,ns_ttl)'
            last_sql = ' VALUES ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")'
            sql = first_sql + last_sql
            db.update_no_commit(sql % (domain, insert_time,last_updated,ips,ips_ttl,ips_geo,cnames,cnames_ttl,ns,ns_ttl))

        if count % 1000 == 0:
            db.commit()
            count = 0

    db.commit()
    db.close()


def domain2tb(check_domain):
    """ 根据域名的首字母，选择存储的数据库表名称"""
    first_name = check_domain[0]
    tb_name = ['0jqxyz','16kouv','2efghr','378lnw','459dip','acsmtb']
    for tb in tb_name:
        if first_name in tb:
            return tb+'_history'

if __name__ == '__main__':
    insert_domains_history()
    # insert_index_domains()















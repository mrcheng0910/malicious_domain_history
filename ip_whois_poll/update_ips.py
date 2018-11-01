
from general_tool.db_conn import DBConn

LOAD_TABLE='domain_rc_ttl'
STORE_TABLE="ip_whois_history"

def load_source():

    db = DBConn()
    db.get_mongo_conns(num=1)
    result=db.mongo_conn[LOAD_TABLE].find(
        {},{'dns_rc':1,'_id':0}
    )
    ips=set()
    for rs in result:
        for row in rs['dns_rc']:
            ips|=set(row['ips'])
    for ip in ips:
        db.mongo_conn[STORE_TABLE].update_one(
            {'ip':ip},
            {
                '$set':{
                    'ip':ip
                }
            },
            upsert=True
        )
    del db
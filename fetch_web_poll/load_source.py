#-*- coding: utf8 -*-

from general_tool.db_conn import DBConn

LOAD_TABLE='domain_index'
STORE_TABLE1="web_history"
STORE_TABLE2="web_lastest"

def load_source():

    db = DBConn()
    db.get_mysql_conns(num=1)
    SQL="select domain,malicious_type,malicious_flag from domain_index"
    db.exec_sql(SQL)
    result=db.mysql_cur.fetchall()
    db.get_mongo_conns(num=1)
    for i,rs in enumerate(result):
        domain, malicious_type, malicious_flag=rs
        print '{seq}:{domain}'.format(seq=i+1,domain=domain)
        db.mongo_conn[STORE_TABLE1].update_one(
            {'domain':domain},
            {
                '$set':{
                    'malicious_type':malicious_type,
                    'malicious_flag':malicious_flag
                }
            },
            upsert=True
        )
        db.mongo_conn[STORE_TABLE2].update_one(
            {'domain':domain},
            {
                '$set':{
                    'malicious_type':malicious_type,
                    'malicious_flag':malicious_flag
                }
            },
            upsert=True
        )
    db.close_mysql_conns()

if __name__=="__main__":
    load_source()
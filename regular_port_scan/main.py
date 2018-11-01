#-*- coding: utf8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf8")
import pickle
import time
import commands
import datetime
import random
from settings import PORTS,LOAD_TABLE,STORE_TABLE1,STORE_TABLE2
from general_tool.db_conn import DBConn
from port_scan import port_scan,get_scan_results
from update_ips import load_source

def exper():

    with open('exper_ip_list.txt','rb') as f:
       ips=set([line.strip() for line in f.readlines()])
    port_scan(ips,PORTS)#扫描ips下的ports情况
    result_file_name=get_scan_results()
    with open(result_file_name,'rb') as f:
        result=pickle.load(f)

    return result

def load_items(start,num):

    print "导出数据..."
    db=DBConn()
    db.get_mongo_conns(num=1)
    res=db.mongo_conn[LOAD_TABLE].find({},{'v_times':1,'_id':0})
    res=list(set([rs['v_times'] for rs in res if 'v_times' in rs]))
    if len(res)<=1:
        print "更新源..."
        load_source()
        print "重新导入数据"
        result = db.mongo_conn[LOAD_TABLE].find(
            {}, {'ip': 1, '_id': 0}
        ).limit(num).skip(start)
    else:#继续上中断位置
        print "载入上次数据"
        print list(res)
        result=[]
        for i in range(max(res)-1,0,-1):
            result = list(db.mongo_conn[LOAD_TABLE].find(
                {'v_times': i}, {'ip': 1, '_id': 0}
            ).limit(num).skip(start))
            if len(result)!=0:
                break
        if len(result)==0:
            result = db.mongo_conn[LOAD_TABLE].find(
                {}, {'ip': 1, '_id': 0}
            ).limit(num).skip(start)
    items=[rs['ip'] for rs in result]
    random.shuffle(items)
    print "导出%d条记录" % len(items)

    return items

def main(st,total_num):

    start = time.time()
    ips=load_items(st,total_num)
    print "端口扫描..."
    port_scan(ips,PORTS)
    print "存储结果..."
    result_file_name=get_scan_results()
    with open(result_file_name,'rb') as f:
        result=pickle.load(f)
    db=DBConn()
    db.get_mongo_conns(num=1)
    for ip in ips:
        row={'ip':ip}
        open_ports=[]
        for key,value in result.iteritems():
            if ip in value:
                row[str(key)] = 'open'
                open_ports.append(str(key))
            else:
                row[str(key)] ='closed'
        row['detect_time']=datetime.datetime.now()
        db.mongo_conn[STORE_TABLE1].update_one(#更新历史表
            {'ip':ip},
            {
                '$inc': {
                    'v_times': 1
                },
                '$set':{
                    'lastest_detect_time': row['detect_time'],
                    'open_ports':'/'.join(open_ports)
                },
                '$addToSet': {
                    'row': row
                }
            },
            upsert=True
        )
        db.mongo_conn[STORE_TABLE2].update_one(#更新最新表
            {'ip':ip},
            {
                '$set':dict(row,**{'open_ports':'/'.join(open_ports)})
            },
            upsert = True
        )
    print commands.getoutput('rm {file_name}'.format(file_name=result_file_name))
    end = time.time()
    print 'runs %0.2f seconds.' % (end - start)

if __name__ == "__main__":
    main(0,1000000)

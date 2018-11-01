# -*- coding: utf8 -*-

"""
WEB数据获取主程序
"""
import os
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import time
import datetime
import random
from general_tool.db_conn import DBConn
from update_ips import load_source
from ip_as import get_asinfos
from ip_whois import get_whoisinfos
from multiprocessing import Queue
from multiprocessing import Process

LOAD_TABLE="ip_whois_history"
STORE_TABLE1="ip_whois_history"
STORE_TABLE2="ip_whois_lastest"

def load_items(num):

    print "导出数据..."
    db=DBConn()
    db.get_mongo_conns(num=1)
    res=db.mongo_conn[LOAD_TABLE].find({},{'v_times':1,'_id':0})
    res=set([int(rs['v_times']) for rs in res if 'v_times' in rs])
    print res
    if len(res)<=1:
        print "更新源..."
        load_source()
        print "导出新纪录"
        result = db.mongo_conn[LOAD_TABLE].find(
            {}, {'ip': 1, '_id': 0}
        ).limit(num)
    else:#继续上中断位置
        print "导出上一次末记录"
        result=[]
        for i in range(max(list(res))-1,0,-1):
            result = list(db.mongo_conn[LOAD_TABLE].find(
                {'v_times':i}, {'ip': 1, '_id': 0}
            ).limit(num))
            if len(result)!=0:
                break
    items=[rs['ip'] for rs in result]
    # print items
    random.shuffle(items)
    print "导出%d条记录" % len(items)

    return items

def task(thread_id,ip_q,as_q,whois_q):

    print 'Run task %s (%s)...' % (thread_id, os.getpid())
    start = time.time()
    db=DBConn()
    db.get_mongo_conns(num=1)
    print "获取as信息..."
    get_asinfos(ip_q, as_q)
    print "获取whois信息..."
    get_whoisinfos(as_q, whois_q)
    print "保存whois信息..."
    flag = True
    while flag:
        while not whois_q.empty():
            whois_info=whois_q.get()
            if whois_info=="quit":
                print "[%d]:quit ip whois"%thread_id
                flag=False
                break
            db.mongo_conn[STORE_TABLE1].update_one(
                {'ip':whois_info['ip']},
                {
                    '$addToSet': {
                        'row': whois_info
                    },
                    '$inc':{
                        'v_times':1
                    },
                    '$set': dict(
                        detect_time=datetime.datetime.now()
                    )
                },
                upsert=True
            )
            db.mongo_conn[STORE_TABLE2].update_one(
                {'ip':whois_info['ip']},
                {'$set': dict(whois_info,
                                **dict(detect_time=datetime.datetime.now())
                                )},
                upsert=True
            )
        print "prequit..."
    print "quit!"
    end = time.time()
    print 'Task %s runs %0.2f seconds.' % (thread_id, (end - start))

def main(num,threads_num):
    """
    
    :param num: ip数量
    :param threads_num: 进程数
    :return: 
    """
    ip_q=Queue()
    as_q=Queue()
    whois_q=Queue()
    items=load_items(num)
    for item in items:
        ip_q.put(item)
    process_list = [Process(target=task, args=(i, ip_q,as_q,whois_q))
                        for i in range(threads_num)]
    print 'Waiting for all subprocesses start...'
    for p in process_list:
        p.start()
    print 'Waiting for all subprocesses done...'
    for p in process_list:
        p.join()
    print "done"

if __name__=='__main__':
    # print load_items(1,2)
    #[u'103.239.29.57', u'103.239.29.56']
    import sys
    flag=True
    if len(sys.argv)!=3:
        print "paras: ip_num process_num"
        sys.exit(-1)
    else:
        total_num,process_num=sys.argv[1],sys.argv[2]
        if (total_num.isdigit() and process_num.isdigit()
            and total_num > 0 and process_num > 0):
            total_num, process_num=int(total_num), int(process_num)
            count=0
            while True:
                count+=1
                start = time.time()
                print "ip_num is %d,process num is %d" % (total_num, process_num)
                print "the %dth run spider web information start"%count
                main(total_num, process_num)
                print "the %dth run spider web information end"%count
                end = time.time()
                print 'total num of ips:%d,process num:%d,runs %0.2f seconds.' % (total_num,process_num,(end - start))
                if flag and count==1:
                    break
        else:
            print "参数输入错误!"
            print "paras: ip_num process_num"
            print total_num,process_num
            sys.exit(-1)
    """
     100个ip 两个进程 59.00 seconds.
    """
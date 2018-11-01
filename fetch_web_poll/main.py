# -*- coding: utf8 -*-

"""
WEB数据获取主程序
"""
import os
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import time
import socket
import nmap
import random
import commands
from webinfoextract.webextract import WebInfoSpider
from general_tool.multi_process import multi_run
from general_tool.db_conn import DBConn
from settings import LOAD_TABLE,STORE_TABLE1,STORE_TABLE2
from settings import DRIVER_NAME,BAN_IMAGES,HEADLESS,SHOT_DIRNAME,ITEMS_FILE
from settings import MAX_TIMEOUT_SECONDS,WAIT_SECONDS,CLOSED_DRIVER_PERIOD

def get_protocol_bynmap(ip):
    """
    功能:扫描ip 80,443，获取端口状态,进而得知网站开放的情况
    param ip:要扫描的ip
    return "http"/"https"/""
    """
    if ip:
        try:
            nm = nmap.PortScanner()
            res = nm.scan(ip, '80,443')
            time.sleep(0.5)
            if res['scan']:
                results = res['scan'][ip]
                ip_info = {}
                ip_info['host_status'] = results['status']['state']
                tcps = [(port, info['state']) for port, info in results['tcp'].iteritems()]
                for port, status in tcps:
                    if port == 21:
                        ip_info['ftp_status'] = status
                    elif port == 53:
                        ip_info['dns_status'] = status
                    elif port == 80:
                        ip_info['http_status'] = status
                    elif port == 443:
                        ip_info['https_status'] = status
                    else:
                        ip_info['http_proxy8080'] = status
                if ip_info.get("http_status") == "open":
                    return "http"
                elif ip_info.get("https_status") == "open":
                    return "https"
        except Exception,e:
            print e
    return ""

def load_items(start,num):

    print "开始导出数据..."
    db = DBConn()
    db.get_mongo_conns(num=1)
    res = list(db.mongo_conn[LOAD_TABLE].find({}, {'v_times': 1, '_id': 0}))
    res = list(set([rs['v_times'] for rs in res if 'v_times' in rs]))
    if len(res) <= 1:
        print "导入新数据"
        result = list(db.mongo_conn[LOAD_TABLE].find(
            {}, {'domain': 1, '_id': 0}
        ).limit(num).skip(start))
    else:  # 继续上中断位置
        print "载入上一次末数据"
	print res
        result=[]
        for i in range(max(res)-1,0,-1):
            result = list(db.mongo_conn[LOAD_TABLE].find(
                {'v_times': i}, {'domain': 1, '_id': 0}
            ).limit(num).skip(start))
            if len(result)!=0:
                break
        if len(result)==0:
            result = list(db.mongo_conn[LOAD_TABLE].find(
                {}, {'domain': 1, '_id': 0}
            ).limit(num).skip(start))
    print "开始解析及获取端口开放情况..."
    items = [rs['domain'] for rs in result]
    random.shuffle(items)
    print "导出%d条记录" % len(items)

    return items

def task(process_id,share_q):

    print 'Run task %s (%s)...' % (process_id, os.getpid())
    start = time.time()
    db=DBConn()
    db.get_mongo_conns(num=1)
    paras_dict = dict(
        closed_period=CLOSED_DRIVER_PERIOD,
        shot_dirname=SHOT_DIRNAME,
        max_time=MAX_TIMEOUT_SECONDS,
        wait_time=WAIT_SECONDS,
        ban_image=BAN_IMAGES,
        headless=HEADLESS
    )
    wis = WebInfoSpider(DRIVER_NAME,**paras_dict)
    count=0
    if isinstance(share_q,list):
        print len(share_q)
    else:
        print share_q.qsize()
    while (isinstance(share_q,list) and len(share_q)) or (hasattr(share_q,'empty') and not share_q.empty()):
        count+=1
        if isinstance(share_q,list):
            item = share_q.pop(0)
        else:
            item = share_q.get()
        domain=item
        try:
            ip = socket.gethostbyname(domain)
        except Exception:
            ip = ""
        protocol = get_protocol_bynmap(ip)
        result=wis.main(domain,protocol=protocol)
        print "{0}:{1}:{2}:{3}:{4}".format(process_id,count, domain,ip,result['web_status'])
        db.mongo_conn[STORE_TABLE1].update_one(
            {'domain':domain},
            {
                '$inc': {
                    'v_times': 1
                },
                '$set':{
                    'lastest_detect_time': result['cur_time'],
                    'ip':ip
                },
                '$addToSet': {
                    'row': result
                }
            },
            upsert=True
        )
        db.mongo_conn[STORE_TABLE2].update_one(
            {'domain':domain},
            {
                '$set':{
                    'ip':ip,
                    'cur_domain': result['cur_domain'],
                    'current_url': result['current_url'],
                    'top_title': result['top_title'],
                    'keywords': result['keywords'],
                    'description': result['description'],
                    'remoteIP': result['cur_ip'],
                    'remotePort': result['cur_port'],
                    'web_status':result['web_status'],
                    'timeout_flag': result['timeout_flag'],
                    'alert_flag': result['alert_flag'],
                    'http_code': result['http_code'],
                    'redirect': result['redirect'],
                    'protocol': result['protocol'],
                    'iframe_num': result['iframe_num'],
                    'images_num': len(result['img_srcs']),
                    'inter_urls_num': len(result['inter_urls']),
                    'outer_urls_num': len(result['outer_urls']),
                    'hidden_domains_num': len(result['hidden_domains']),
                    'outer_domains_num': len(result['outer_domains']),
                    'shot_path': result['shot_path'],
                    'img_srcs': result['img_srcs'],
                    'inter_urls': result['inter_urls'],
                    'outer_urls': result['outer_urls'],
                    'hidden_domains': result['hidden_domains'],
                    'outer_domains': result['outer_domains'],
                    'titles': result['titles'],
                    'metas': result['metas'],
                    'inter_urls_texts': result['inter_urls_texts'],
                    'outer_urls_texts': result['outer_urls_texts'],
                    'images_alts':  result['img_alts'],
                    'detect_time':result['cur_time']
                }
            },
            upsert=True
        )
    wis.driverhandler.destory_driver()
    del wis,db
    end = time.time()
    print 'Task %s runs %0.2f seconds.' % (process_id, (end - start))

if __name__=='__main__':
    flag=False
    if len(sys.argv)==4:
        start,total_num,process_num=sys.argv[1],sys.argv[2],sys.argv[3]
        if (total_num.isdigit() and process_num.isdigit()and start.isdigit()
            and total_num > 0 and process_num > 0 and start>=0):
            start,total_num, process_num=int(start),int(total_num), int(process_num)
            count=0
            while True:
                count+=1
                t1 = time.time()
                print "domain_num is %d,process num is %d" % (total_num, process_num)
                print "the %dth run spider web information start"%count
                multi_run(source_data=load_items(start,total_num), task=task, process_num=process_num, mode=1)
                print "the %dth run spider web information end"%count
                t2 = time.time()
                print 'total num of domains:%d,process num:%d,runs %0.2f seconds.' % (total_num,process_num,(t2 - t1))
                if os.path.isfile(ITEMS_FILE):
                    print commands.getoutput('rm {file_name}'.format(file_name=ITEMS_FILE))
                if flag and count==3:
                    break
        else:
            print "参数输入错误!"
            print "paras: start domain_num process_num"
            print start,total_num,process_num
            sys.exit(-1)
    else:
        print "paras: start domain_num process_num"
        sys.exit(-1)

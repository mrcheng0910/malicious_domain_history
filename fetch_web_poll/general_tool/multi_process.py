# -*- coding: utf8 -*-

"""
WEB数据获取主程序
"""
# from multiprocessing import Manager
from multiprocessing import Process
from multiprocessing import Pool
from multiprocessing import Queue
import os, time
import sys

def divide_items(items,num):

    if not items or not isinstance(items,list) or not isinstance(num,int):
        print "items is None or items is not list instance or type of paras is error!"
        sys.exit(-1)
    print "divide items to %d sections"%num
    trader = len(items)//num #商
    remainder = len(items)%num #余数
    A = items[:trader*num]
    if remainder!=0:
        B = items[trader*num:]
    else:
        B = []
    index = 0
    results = []
    while index<trader*num:
        results.append(A[index:index+trader])
        index = index+trader
    results[-1].extend(B)

    return results

def long_time_task(process_id,para,name):

    print "<======this is a %s example=======>"%name
    print 'Run task %s (%s)...' % (process_id, os.getpid())
    start = time.time()
    if not isinstance(para,list):
        q=para
        while not q.empty():
            item = q.get()
            print item
            time.sleep(1)
    else:
        for item in para:
            print item
            time.sleep(1)
    end = time.time()
    print 'Task %s runs %0.2f seconds.' % (process_id, (end - start))
    print "<======this is a %s example=======>"%name

def multi_run(*args,**kwargs):

    if kwargs.get('mode') and kwargs.get('mode') not in (1,2):
        print "mode is error!"
        sys.exit(-1)
    mode = kwargs['mode'] if kwargs.get('mode') else (1)
    source_data = kwargs.get('source_data')
    task = kwargs.get('task')
    process_num = kwargs.get('process_num')
    if process_num is None or not (process_num and isinstance(process_num,int)):
        process_num=4
    print 'Parent process %s.' % os.getpid()
    if mode==1:
        print "start share queue..."
        q = Queue()
        if task is None:
            task = long_time_task
            source_data = range(process_num)
        for item in source_data:
            q.put(item)
        process_list=[Process(target=task, args=(i, q,) + args) for i in range(process_num)]
        print 'Waiting for all subprocesses start...'
        for p in process_list:
            p.start()
        print 'Waiting for all subprocesses done...'
        for p in process_list:
            p.join()
    else:
        print "start process pool..."
        p = Pool()
        if task is None:
            task = long_time_task
            source_data = list(range(process_num))
        sections = divide_items(source_data, process_num)
        print 'Waiting for all subprocesses start...'
        for i,item in enumerate(sections):
            p.apply_async(task, args=(i,item)+args)
        print 'Waiting for all subprocesses done...'
        p.close()
        p.join()
    print 'All subprocesses done.'

if __name__=='__main__':
    multi_run('test',mode=1)
#-*- coding: utf8 -*-

import os
import commands
import pickle
from settings import DATA_RESULT_DIRECTORY

def port_scan(ips,ports):
    """
    多端口扫描
    :param ips: 
    :param ports: 
    :return: 
    """
    ips=list(ips)
    for i,port in enumerate(ports):
        print "scan %d port open/closed..."%port
        single_port_scan(ips,port)

def single_port_scan(ips,port):
    """
    扫描指定端口的开放情况
    :param ips: 待扫描ip集合
    :param port: 指定端口
    :return: 
    """
    print "**************begin:scan %d****************" % port
    if not os.path.exists(DATA_RESULT_DIRECTORY):
        os.mkdir(DATA_RESULT_DIRECTORY)
    result_fn = '{pro_path}/{port}_result.txt' \
                   ''.format(pro_path=DATA_RESULT_DIRECTORY,port=port)
    seg_result_fn = '{pro_path}/{port}_seg_result.txt' \
                   ''.format(pro_path=DATA_RESULT_DIRECTORY, port=port)
    f = open(result_fn, 'a+')
    for i in range(0,len(ips),100):
        end = i+100 if i+100<len(ips) else(len(ips))
        cmd = 'zmap -p {port} -B 5M -o {file_name} {ips_list}'.format(
            port=port,file_name=seg_result_fn,ips_list=' '.join(ips[i:end])
        )
        commands.getoutput(cmd)
        print "***"+str(end)+"***"
        with open(seg_result_fn,'rb') as fb:
            j=0
            for k in fb.readlines():
                if j==0:
                    f.write(k.strip())
                else:
                    f.write('\n'+k.strip())
                j+=1
        if end==len(ips):break
    f.close()
    if os.path.isfile(seg_result_fn):
        print commands.getoutput('rm {file_name}'.format(file_name=seg_result_fn))
    print "**************end:scan %d****************"%port

def get_scan_results():
    """
    获取格式化的扫描结果
    print root  # 当前目录路径
    print dirs  # 当前路径下所有子目录
    print files  # 当前路径下所有非目录子文件
    :return: 
    """
    result_fn=DATA_RESULT_DIRECTORY+'/result.pkl'
    if not os.path.exists(DATA_RESULT_DIRECTORY):
        os.mkdir(DATA_RESULT_DIRECTORY)
    dic={}
    for root, dirs, files in os.walk(DATA_RESULT_DIRECTORY):
        for file in files:
            port=file.split('_')[0]
            dic.setdefault(port,[])
            fn=DATA_RESULT_DIRECTORY+'/'+file
            with open(fn,'rb') as f:
                for line in f.readlines():
                    dic[port].append(line.strip())
            print commands.getoutput('rm {file_name}'.format(file_name=fn))
    with open(result_fn, 'wb') as f:
        pickle.dump(dic, f)

    return result_fn

if __name__ =="__main__":
    pass
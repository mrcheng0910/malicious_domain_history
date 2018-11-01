#coding=utf-8

import socket

def get_ipasinfo(query_ip):
    """
    获取ip的as信息
    :param query_ip: ip
    :return: as信息
    """
    ip_as = ''
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(10)
        conn.connect(('38.229.36.122', 43))
        conn.send((
                      ' -r -a -c -p -f {0}{1}'.format(
                          query_ip, '\r\n')
                  ).encode())
        data=""
        while True:
            elem = conn.recv(4096).decode()
            data += elem
            if not elem: break
        as_info = data.replace(' ', '')
        ip_as = as_info.split("|")
        asn = ip_as[0]
        ip = ip_as[1]
        as_cidr = ip_as[2]
        date = ip_as[5]
        as_country_code = ip_as[3]
        as_description = ip_as[6]
        rir = ip_as[4]
        ip_as = {
            'ip': ip,
            'asn': asn,
            'asn_cidr': as_cidr,
            'asn_country_code': as_country_code,
            'rir': rir,
            'date': date,
            'asn_description': as_description
        }
    except Exception:
        pass

    return ip_as

def get_asinfos(ip_q,as_q):
    """
    将ip_q队列中的ip的as信息存放到as_q队列中
    :param ip_q: 存放ip的队列
    :param as_q: 存放as的队列
    :return: 
    """
    count=0
    while not ip_q.empty():
        query_ip = ip_q.get()
        count+=1
        print "{0}:{1}".format(count,query_ip)
        ip_as=get_ipasinfo(query_ip)
        if ip_as:
            as_q.put(ip_as)
        else:
            ip_as={'asn_country_code': "", 'ip': query_ip,
                   'rir':"", 'asn_cidr': "", 'date': "",
                   'asn':"", 'asn_description': ""}
            as_q.put(ip_as)
    as_q.put('quit')#结束标志

if __name__=="__main__":
    query_ip='104.28.24.105'#'156.235.233.245'
    print get_ipasinfo(query_ip)
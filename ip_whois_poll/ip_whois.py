#coding=utf-8

import socket
import re

RIR_WHOIS = {
    'arin': {'server': '199.71.0.46'},
    'lacnic':{'server': '200.3.14.10'},
    'ripe': {'server': '193.0.6.135'},
    'apnic': {'server': '202.12.29.220'},
    'afrinic': {'server': '196.216.2.20'},
}

def get_ipwhoisinfo(query_ip,rir):
    """
    通过ip和rir信息获取ip的whois信息
    :param query_ip: ip
    :param rir: rir
    :return: whois信息
    """
    data = ''
    try:
        server = RIR_WHOIS[rir]['server']
        # Create the connection for the whois query.
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(10)
        conn.connect((server, 43))
        # Prep the query.
        query = query_ip + '\r\n'
        # Query the whois server, and store the results.
        conn.send(query.encode())
        while True:
            try:
                elem = conn.recv(4096).decode('ascii', 'ignore')
                data += elem
                if not elem:break
            except Exception:
                '''error: [Errno 104] Connection reset by peer'''
                conn.settimeout(10)
                conn.recv(4096).decode('ascii', 'ignore')
        conn.close()
    except Exception:
        pass

    return data

def parse_whois(whois_dict):

    if not whois_dict:
        return ""
    ini_whois_info_sector = whois_dict.split("\n\n")
    sector_names = []
    ip_whois = {}
    whois_info_sector = []

    for whois_sector in ini_whois_info_sector:

        if len(whois_sector) and whois_sector[0].isalpha():

            sector_name = whois_sector.split(': ')[0]
            sector_name = sector_name.strip()
            sector_name = sector_name.replace(".", "")
            if sector_name:
                sector_names.append(sector_name)
            if whois_sector:
                whois_sector += '\n---'
                whois_info_sector.append(whois_sector)

    for sector, whois_sector in zip(sector_names, whois_info_sector):
        lines = whois_sector.split('\n')

        # for sector,whois_sector in zip(sector_names,whois_info_sector):
        temp = {}
        # 临时存储当前一段的内容

        '''以下是对一个object的处理 '''
        for line in lines:

            if line != '---' and line != '':
                '''
                r': +'(两个空格)，为了避免错误提取/Original nic-hdl in AUNIC: DP5-AU/中AUNIC: DP5-AU的部分
              '''
                temp_split = str(re.split(r':  +', line))
                temp_split = temp_split.replace(".", "")

                # Taipei Taiwan 这种情况下line[0] == ' '
                if line[0] != ' ':
                    item_name1 = temp_split.split("'")
                    item_name = item_name1[1]

                    # regex = item_name + r':[^\S]+(.*)'
                    # 把 + 改为 * 说明冒号可以直接和后面data相连没有空格
                    regex = item_name + r':[^\S]*(.*)'
                    item_value = re.compile(regex, re.I).findall(line)
                    '''
                    eg. arin-174.139.55.107 存在一个comment内容为空
                    Found a referral to vault.krypt.com:4321.提取有误
                '''
                    item_value = item_value[0].strip() if item_value else ''

                    if item_name not in temp.keys():
                        temp[item_name] = item_value
                    else:
                        if isinstance(temp[item_name], list):
                            temp[item_name].append(item_value)
                        else:
                            temp[item_name] = [temp[item_name]]
                            temp[item_name].append(item_value)

                elif line[0] == ' ':
                    item_value = line.strip()
                    if not isinstance(temp[item_name], list):
                        # 此时的item_name还与上一次的相同
                        temp[item_name] = temp[item_name] + ' ' + item_value
                    elif isinstance(temp[item_name], list):
                        length = len(temp[item_name])
                        temp[item_name][length - 1] += item_value

        '''将处理好的一个对象的信息，加入到ipwhois信息的字段中'''
        if sector not in ip_whois.keys():
            ip_whois[sector] = temp
        else:
            if isinstance(ip_whois[sector], list):
                ip_whois[sector].append(temp)
            else:
                ip_whois[sector] = [ip_whois[sector]]
                ip_whois[sector].append(temp)

    return ip_whois

def get_whoisinfos(as_q,whois_q):
    """
    通过as_q队列中的ip,rir,获取whois信息,并存放到whois_q队列中
    :param as_q: 存放rir信息的队列
    :param whois_q: 存放whois信息的队列
    :return: 
    """
    flag=True
    count=0
    while flag:
        while not as_q.empty():
            count+=1
            ip_as=as_q.get()
            if ip_as=="quit":
                print "quit as"
                flag=False
                break
            print "{0}:{1}".format(count,ip_as['ip'])
            parsed_whois=""
            if ip_as['rir']:
                whois_info = get_ipwhoisinfo(ip_as['ip'], ip_as['rir'])
                try:
                    parsed_whois = parse_whois(whois_info)
                except Exception:
                    pass
            if parsed_whois and isinstance(parsed_whois,dict):
                ip_as['ip_whois']=parsed_whois
                whois_q.put(ip_as)
            else:
                ip_as['ip_whois'] = {}
                whois_q.put(ip_as)
        print "prequit..."
    whois_q.put("quit")
    print "quit!"

def exper():
    from ip_as import get_ipasinfo
    ip_as=get_ipasinfo('156.235.233.245')
    whois_info=get_ipwhoisinfo(ip_as['ip'],ip_as['rir'])
    parsed_whois= parse_whois(whois_info)
    print parsed_whois.keys()

if __name__=="__main__":
    exper()
# encoding:utf-8
"""
统计IP的地理位置信息
IP定位数据来源于github（https://github.com/lionsoul2014/ip2region）
"""

from ip_location.ip2Region import Ip2Region

searcher = Ip2Region('./ip_location/ip2region.db')  # IP定位


def ip2region(ip=None):
    """
    得到IP的地理位置和运营商
    :param ip: 待查询IP
    :return
        city: ip所在城市，若城市为空，则为国家
        network_operator: 运营商，可能为空
    """
    if ip == "" or ip is None:
        return

    data = searcher.btreeSearch(ip)
    data = data['region'].split('|')
    return dict(
        country = data[0],
        region = data[2],
        city = data[3],
        oper = data[4]
    )


if __name__ == '__main__':
    print ip2region('203.195.130.175')['region']
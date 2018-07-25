# encoding: utf-8
"""
mongodb基础数据库
"""

from pymongo import MongoClient

server_address = '10.245.146.37'


def get_db(db_name = 'malicious_domain_history'):
    """
    连接数据库
    :return
    """
    client = MongoClient(server_address, 27017)
    db = client[db_name]
    return db


def get_col(col_name='keyinfo',db_name='malicious_domain_history'):
    """
    获取collection
    :return: col
    """
    db = get_db(db_name)
    col = db[col_name]
    return col
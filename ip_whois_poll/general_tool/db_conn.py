#-*- coding: utf8 -*-

import MySQLdb
from settings import MONGO_SETTINGS,MYSQL_SETTINGS
from pymongo import MongoClient

class DBConn():
    """
    数据库连接接口
    """
    def __init__(self,*args,**kwargs):

        self.threads_num=kwargs.get('threads_num') if 'threads_num' in kwargs else(1)
        self.mysql_settings=MYSQL_SETTINGS
        self.mongo_settings=MONGO_SETTINGS

    def get_mysql_conns(self,num=0):

        threads_num = self.threads_num if num <= 0 else(num)
        mysql_conns = []
        mysql_curs=[]
        for i in range(threads_num):
            conn = MySQLdb.connect(
                host=self.mysql_settings['host'],
                user=self.mysql_settings['user'],
                port=self.mysql_settings['port'],
                passwd=self.mysql_settings['passwd'],
                db=self.mysql_settings['db'],
                charset=self.mysql_settings['charset']
            )
            cur=conn.cursor()
            mysql_conns.append(conn)
            mysql_curs.append(cur)
        if threads_num==1:
            self.mysql_conn = mysql_conns[0]
            self.mysql_cur=mysql_curs[0]
        else:
            self.mysql_conns = mysql_conns
            self.mysql_curs=mysql_curs

    def get_mongo_conns(self,num=0):

        threads_num = self.threads_num if num <= 0 else(num)
        mongo_conns = []
        for i in range(threads_num):
            mongo_conns.append(
                MongoClient(
                    self.mongo_settings['mongo_ip'],
                    self.mongo_settings['mongo_port']
                )[self.mongo_settings['mongo_db']]
            )
        if threads_num==1:
            self.mongo_conn = mongo_conns[0]
        else:
            self.mongo_conns = mongo_conns

    def close_mysql_conns(self):

        if hasattr(self,"mysql_conn"):
            try:
                self.mysql_cur.close()
                self.mysql_conn.close()
            except Exception:
                pass
        if hasattr(self,"mysql_conns"):
            try:
                for mysql_cur,mysql_conn in zip(self.mysql_curs,self.mysql_conns):
                    mysql_cur.close()
                    mysql_conn.close()
            except Exception:
                pass

    def exec_sql(self,sql,data=None):

        if hasattr(self,'mysql_cur'):
            try:
                if data and isinstance(data,tuple):
                    self.mysql_cur.execute(sql,data)
                else:
                    self.mysql_cur.execute(sql)
            except Exception, e:
                print e
                self.mysql_conn.rollbakc()
        else:
            print "mysql is go always!"
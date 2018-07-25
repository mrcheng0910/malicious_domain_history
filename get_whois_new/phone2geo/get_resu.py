# coding=utf-8
'''
基于数据结构对电话进行解析
'''
import  MySQLdb
import re
from hashmap1 import MyHash
from  format_phone import Deal_phone
from  qianduan_format import WebFormat
import sys
reload(sys)
sys.setdefaultencoding('utf8')

'''
输入一个电话，
输出这个电话的标准格式、地理位置、类型、是否中国（0表示中国，1不是，但有些是中国的号码，可能国际代码处写的国外的）
'''

class GetRes(object):
    def __init__(self):
        self.myhash = MyHash()
        self.dealphone=Deal_phone()
        self.file_object = open('./phone2geo/phone.txt', 'rb') #手机号
        self.lines = self.file_object.readlines()
        self.file_object.close()
    ##将供手机号码解析的地理位置源录入hashmap中
    def ini(self):
        for line in self.lines:
            s=line.strip().split('\t')
            code=int(s[0])
            pro=s[1]
            city=s[2]
            self.myhash.insert(code, pro, city)

    ##根据手机号码的前7位，返回对应的地理位置
    def phone_pos(self,code):
        li=self.myhash.get(code)
        if(li):
            return li
        else:
            return None

    ##找固定电话的地理位置,此处的phone_right一定是首位为0的
    def tel_pos(self,phone_right):
        flag=0
        for i in self.dealphone.list_tel:
            quhao = i[0]
            length = len(quhao)
            phone_quhao = phone_right[0:length]  # 补0之后的区号位
            if (quhao == phone_quhao):  # 存在该区号，说明为固定电话
                flag = 1
                return i[1],i[2]
        if (flag== 0):
            return None

    #输入任意给定的电话，返回地理位置及标准格式
    def analysis_phone(self,phone):
        global country_flag1  # 表示是否为中国的,0表示外国，1表示中国
        global phone_type  # 表示电话解析类型
        flag1 = 0
        phone_type = 0
        s='0'
        pro=None
        city=None
        form_pho=self.dealphone.get_type(phone)
        format_phone=form_pho[1]
        phone_left=format_phone.split('.')[0]
        # print(phone)
        # print(phone_left)
        phone_right=format_phone.split('.')[1]
        phone_length=len(phone_right)
        phone_right_fir=phone_right
        if (phone_left == "+86"):
            flag1 = 1
        if(phone_left=="-1"):
            flag1=2
        if(flag1==1):
            if (phone_length >= 2):
                # 先当固话处理 无0先加上0
                if (phone_right[0] != '0'):
                    phone_right = s + phone_right
                    phone_type = 2
                elif (phone_right[0:2] == '00'):
                    phone_right = phone_right[1:]
                    phone_type = 3
                else:
                    if (len(phone_right) == 11 or len(phone_right) == 12):
                        phone_type = 1
                    else:
                        phone_type = 4
                if (phone_right[1] == '0'):  # 最多去完两0之后还是0，则直接当解析失败
                    phone_type = 7
                if(phone_type!=7):
                    if (len(phone_right) >= 3):
                        locations = GetRes.tel_pos(self, phone_right)
                        if (locations):
                            pro = locations[0]
                            city = locations[1]
                            l = WebFormat()
                            city = l.change_city(pro, city)  # 规范城市名称
                        else:
                            # 当手机号解析
                            if (phone_length >= 7):
                                if (phone_right_fir[0] == '1'):
                                    if (phone_length == 11):
                                        phone_type = 1
                                    else:
                                        phone_type = 2
                                elif (phone_right_fir[0] == '0' and phone_right_fir[1] == '1'):
                                    phone_right_fir = phone_right_fir[1:]
                                    phone_type = 5
                                elif (phone_right_fir[0:2] == '00' and phone_right_fir[3] == '1'):
                                    phone_right_fir = phone_right_fir[2:]
                                    phone_type = 6
                                else:
                                    phone_type = 7
                                if (phone_type != 7):
                                    if (len(phone_right_fir) >= 7):
                                        ##开始解析手机
                                        code = phone_right_fir[0:7]
                                        code = int(code)
                                        locations1 = GetRes.phone_pos(self, code)
                                        if (locations1):
                                            pro = locations1[0]
                                            city = locations1[1]
                                            l = WebFormat()
                                            city = l.change_city(pro, city)
                                        else:
                                            phone_type = 7
                                    else:
                                        phone_type = 7
                            else:
                                phone_type = 7
                    else:
                        phone_type = 7
            else:
                phone_type = 7
        if(flag1==0):
            phone_type=0
        if(flag1==2):
            phone_type=8

        result = {}
        result['province'] = pro
        result['city'] = city
        result['type'] = phone_type
        result['is_china'] = flag1

        return result


def get_phone_locate(phone):
    g = GetRes()
    g.ini()
    phone_locate = g.analysis_phone(phone)
    return phone_locate






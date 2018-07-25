# encoding:utf-8
"""
使用Levenshtein距离初始化字符，利用k-means算法来进行聚类分析
"""

import Levenshtein
import json
import re
from collections import Counter
# from get_whois.data_base import MySQL
# from get_whois.config import SOURCE_CONFIG
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class ProvinceCityObj(object):
    """
    省份和城市名称类
    """

    def __init__(self, original_province, original_city,region_data):

        self.original_province = original_province  # 原始的省份名称
        self.original_city = original_city  # 原始的城市名称
        self.region_data = region_data  # 区域数据

        # 省份相关变量
        self.unconfirmed_province = ""   # 格式化后的未确认省份名称
        self.candidate_provinces = []
        self.confirmed_province = ""   # 匹配的省份名称
        self.province_alias = ""   # 与之匹配的省份名称
        self.province_alias_ratio = 0.0

        # 城市相关变量
        self.unconfirmed_city = ""  # 格式化后的未确认城市名称
        self.candidate_citys = []
        self.confirmed_city = ""  # 匹配的城市名称
        self.city_alias = ""  # 与之匹配的城市名称
        self.city_alias_ratio = 0.0

        # 特殊情况，有多个省份或城市
        self.multiple_province = False
        self.multiple_city = False

    def _process_province_city(self):
        """
        格式化省份和城市名称，去除除数字、字母和汉字的其他内容
        """
        # 删除除数字、字母和汉字等其他内容,可能删除后，剩余为空字符串
        self.unconfirmed_province = self._remove_punctuation(self.original_province).lower()
        self.unconfirmed_city = self._remove_punctuation(self.original_city).lower()

    def _remove_punctuation(self, line):
        """
        提取出数字、字母和汉字，去除其他字符
        :param line: 待处理的字符串
        """
        rule = re.compile(ur"[^a-zA-Z0-9\u4e00-\u9fa5]")
        # line = rule.sub('', unicode(line, "utf-8"))
        line = rule.sub('', line)
        return line


    def _compute_similarity(self,s1, s2):
        """
        s1为要匹配的，s2为标准的格式
        计算相似性两个字符串的相似性
        相似性分为三个等级：
        等级1：完全相同
        等级2：相似度
        等级3：s2存在在s1中
        todo 等级2和等级3的分配是否合理
        """
        # todo 需要对这三种方法的优劣进行分析， 选择最有效的一种计算方法

        # 两个字符串完全相同
        s1,s2 = str(s1),str(s2)
        if s1 == s2:
            similarity_level = 1
            return 1.0, similarity_level

        # 若只有2个字母，则使用相似性进行计算,不能使用index
        if len(s2) <= 2:  # 2或者3 todo 验证
            similarity_level = 2
            return Levenshtein.jaro_winkler(s1, s2, 0.1), similarity_level
        else:
            try:
                s1.index(s2)  # 标准名称是否在待验证的名称中出现，若无则会出现异常
            except ValueError:
                # return Levenshtein.jaro(s1, s2)   # 相似度
                similarity_level = 2
                return Levenshtein.jaro_winkler(s1, s2, 0.1), similarity_level
                # return Levenshtein.distance(s1,s2)  # 距离
                # return Levenshtein.ratio(s1,s2)   # 相似性
            else:
                similarity_level = 3
                return 1.0, similarity_level  # 完全匹配则返回1.0

    def match_candidate_province(self, name):
        """
        与省份/直辖市/自治区/行政区等数据进行比较，根据相似度，匹配出相似的候选项
        :param name string: 待比较的选项
        :return: candidate_provinces dict : 包含匹配的省份名称，所匹配的省份别名，相似度和匹配等级

        """
        candidate_provinces = []
        for prov_name in self.region_data:
            prov_alias = self.region_data[prov_name]['alias']
            for alias in prov_alias:
                province_ratio = {}
                ratio, level = self._compute_similarity(name, alias)  # 相似度和等级
                if ratio >= 0.95:
                    province_ratio["province"] = prov_name
                    province_ratio["alias"] = alias
                    province_ratio["ratio"] = ratio
                    province_ratio["level"] = level
                    candidate_provinces.append(province_ratio)
        candidate_provinces = sorted(candidate_provinces, key=lambda ratio: ratio["ratio"], reverse=True)  # 降序排序
        return candidate_provinces

    def choose_province_city(self):
        """
        得到匹配的省份和对应城市的名称
        """

        self._process_province_city()  # 省份和城市名称格式化处理
        self.candidate_provinces = self.match_candidate_province(self.unconfirmed_province)  # 获取与省份相似的名称和相似度集合
        self.choose_province()  # 获取省份名称和其他情况

        self.match_candidate_city()  # 获取对应省份的相似名称的城市和概率集合
        self.choose_city()

    def choose_province(self):
        """
        选择最准确的省份，以及匹配的省份内容和等级情况
        todo 等级暂时未使用上
        """
        province_counter = Counter() # 统计匹配出的各个省份出现的次数
        if not self.candidate_provinces:  # 如果为空，则结束
            return
        for p in self.candidate_provinces:
            province_counter[p['province']] += 1

        self.confirmed_province,self.multiple_province = self.vote_poll(province_counter,self.candidate_provinces, 'province')

    def vote_poll(self, counter, souce_data, option):
        """
        选择票数最多的候选项
        :param counter: dict 选项和票数分布
        :return:
            most_votes_item: string 得票最多的选项，可能是票数相同多个候选项
            is_same:  bool 是否有相同票数的选项
        """

        items = []  # 候选项
        vote_result = ""
        initial_vote = 0  # 初始票数为0

        # 首先通过计数，来选择合适的选项
        if len(counter) == 1:   # 若只有1个候选项，则直接输出唯一候选项，无相同票数
            vote_result = counter.keys()[0]
            return vote_result, False
        else:  # 多于1个候选项时获取票数最多的选项
            for item, votes in counter.most_common():  # 注意根据票数已对候选项进行了排序
                if votes >= initial_vote:
                    items.append(item)
                    initial_vote = votes
                else:    # 若无，则退出
                    break

            if len(items) >= 2:
                is_same = True   # 有多个选项
            else:
                is_same = False   # 无多个选项
                vote_result = items[0]
                return vote_result, is_same

        # 如果有多个匹配选项，则开始使用level和ratio两个参数
        tmp = []
        for i in souce_data:  # 使用level
            if (i[option] in items) and (i['level'] == 1 or i['level']==3):
                tmp.append(i[option])

        if len(tmp) >= 2:
            is_same = True
        elif len(tmp) == 1:
            is_same = False
        else:
            is_same = True
            tmp = items

        return  ','.join(tmp), is_same

    def match_candidate_city(self):
        """
        得到候选的城市和概率集合
        :param province_region:
        :return:
        """
        # 未匹配到省份，省份为空
        if not self.confirmed_province:
            return

        # 匹配到两个省份
        if self.multiple_province:
            # print "匹配出多个省份",self.confirmed_province.split(',')
            confirmed_province_citys = []

            for p in self.confirmed_province.split(','):
                province_region = self.region_data[p]['city']
                citys = self.match_city(province_region,self.unconfirmed_city)
                confirmed_province_citys.append(citys)
                if citys:
                    self.confirmed_province = p
                    self.candidate_citys = citys
                    break
            return

        province_region = self.region_data[self.confirmed_province]['city']
        self.candidate_citys = self.match_city(province_region,self.unconfirmed_city)

    def match_city(self,province_region,unconfirmed_city):
        """
        获取候选城市列表
        :param province_region:
        :param unconfirmed_city:
        :return:
        """
        candidate_citys = []
        for c in province_region:
            city_alias = province_region[c]
            for i in city_alias:
                city_ratio = {}
                ratio, level = self._compute_similarity(unconfirmed_city, i)
                if ratio >= 0.9:
                    city_ratio["city"] = c
                    city_ratio["alias"] = i
                    city_ratio["ratio"] = ratio
                    city_ratio["level"] = level
                    candidate_citys.append(city_ratio)
        candidate_citys = sorted(candidate_citys, key=lambda ratio: ratio["ratio"], reverse=True)  # 降序排序
        return candidate_citys

    def choose_city(self):
        """
        选择最准确的省份，以及匹配的省份内容和等级情况
        todo 等级暂时未使用上
        """
        city_counter = Counter()  # 统计匹配出的各个省份出现的次数
        if not self.candidate_citys:  # 如果候选城市集合为空，则结束
            return
        for p in self.candidate_citys:
            city_counter[p['city']] += 1

        self.confirmed_city, self.multiple_city = self.vote_poll(city_counter,self.candidate_citys,'city')

    def get_all_feature(self):
        """
        获取所有信息
        """
        return {
            "candidate_provinces": self.candidate_provinces,
            "confirmed_province": self.confirmed_province,
            "candidate_citys": self.candidate_citys,
            "confirmed_city": self.confirmed_city,
            "multiple_province": self.multiple_province,
            "multiple_city": self.multiple_city
        }

    def analyze_feature(self):

        # if self.confirmed_province != "beijing":
        #     return
        print "待匹配的省份和城市为：",self.original_province+","+self.original_city
        if not self.confirmed_province:
            print "没有找到匹配的省份，其待候选的省份列表为："
            print self.candidate_provinces
            return
        else:
            print '匹配的省份为：', self.confirmed_province
        if not self.confirmed_city:
            print "没有找到匹配的城市，原因为："
            if self.multiple_province:
                print "发现匹配出多个省份，无法确认城市"
                return
            else:
                print "其待候选的城市列表为："
                print self.candidate_citys
                return
        else:
            print '匹配的城市为：', self.confirmed_city


def read_province():
    """
    读取省份名称和其别名，以及省份下的城市以及城市名称
    :return:
    """
    with open('../whois_code/province_city1.json','r') as f:
        data = json.load(f)
    return data

def verify_province_city(province_name,city_name):
    """
    验证输入的省份和城市
    :param province_name: 待验证的省份名称
    :param city_name:  待验证的城市名称
    :return:
        result： 返回匹配的结果
    """
    if not province_name:
        return None
    region_data = read_province()  # 标准区域数据
    province_city_obj = ProvinceCityObj(province_name, city_name, region_data)  # 创建对象
    province_city_obj.choose_province_city()  # 选择省份和城市

    verify_results = province_city_obj.get_all_feature()
    # province_city_obj.analyze_feature()

    return verify_results


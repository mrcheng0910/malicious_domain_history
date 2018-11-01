#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

import re
import os
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import json
from urlparse import urljoin
from bs4 import BeautifulSoup
from tldextract import extract
from datetime import datetime
from driver import DriverHandler

class WebInfoSpider():
    """
    页面信息获取
    """
    def __init__(self,drivertype,**kwargs):

        #配置驱动
        self.driverhandler=DriverHandler(drivertype,**kwargs)
        #配置快照路径
        self.shot_dirname=self.set_default(kwargs,'shot_dirname','shot_files')
        #配置regexp模式
        self.url_mode=re.compile(
            r'((http|ftp|https)://)([a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]\.){1,4}[a-zA-Z]{2,6}'
        )
        self.domain_mode=re.compile(
            r'([a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]\.)|([a-zA-Z0-9]\.){1,4}[a-zA-Z]{2,6}'
        )
        self.filter_mode=re.compile(
            r'(.js)|(.css)|(.ico)|(.exe)|(.apk)'
        )
        #重开驱动计数器
        self.counter=0
        self.period=self.set_default(kwargs,'closed_period',40)

    def set_default(self,paras_dict,key,value):

        return value if key not in paras_dict else(paras_dict[key])

    def globe_variable_initializer(self,domain,protocol):
        """
        初始化实例参数
        :param domain: 
        :return: 
        """
        #page sources
        self.all_page_sources=[]
        #web status information
        self.domain=domain
        self.cur_ip=""
        self.cur_port=""
        self.cur_domain = domain
        self.cur_time = datetime.now()
        self.current_url='{protocol}://www.{domain}'.format(
            protocol=protocol,domain=domain
        )
        self.bowser_log=""
        self.protocol=protocol
        self.http_code=""
        self.redirect = ""
        self.timeout_flag=-1
        self.alert_flag=0
        self.web_status='closed'

        #web snapshot information
        self.shot_path = ""
        #web text information
        self.iframe_num = 0
        self.top_title = ""
        self.keywords=""
        self.description=""
        self.titles = []
        self.metas = []
        self.inter_urls_texts = []
        self.outer_urls_texts = []
        self.img_alts = []
        #web link information
        self.inter_urls = []
        self.outer_urls = []
        self.img_srcs = []
        self.hidden_domains = []
        self.outer_domains = []

    def getHttpStatus(self):
        """
        获取http响应码
        :return: 
        """
        if self.driverhandler.driver_type=='chrome':
            try:
                bowser_log =self.driverhandler.driver.get_log('performance')
            except Exception,e:
                self.bowser_log = str(e)
                return
            else:
                for log in bowser_log:
                    try:
                        response = json.loads(log[u'message'])[u'message'][u'params'][u'response']
                        self.cur_ip = response[u'remoteIPAddress']
                        self.cur_port = response[u'remotePort']
                        self.http_code = response[u'status']
                    except:
                        pass
                    else:
                        self.bowser_log=log
        else:
            try:
                har = json.loads(self.driverhandler.driver.get_log('har')[0][u'message'])
                response=har['log']['entries'][0][u'response']
                self.cur_ip = response[u'remoteIPAddress']
                self.cur_port = response[u'remotePort']
                self.http_code = response[u'status']
            except Exception, e:
                self.bowser_log = str(e)

    def snapShot(self,shot=False):
        """
        快照截图
        :return: 
        """
        if shot:
            self.shot_dirname = "shot_files"
        if self.shot_dirname:
            if not os.path.exists(self.shot_dirname):
                os.makedirs(self.shot_dirname)
            directory = '{dir_name}/{year}_{month}_{day}'.format(
                dir_name=self.shot_dirname,
                year=self.cur_time.year,
                month=self.cur_time.month,
                day=self.cur_time.day
            )
            if not os.path.exists(directory):
                os.makedirs(directory)
            shot_path = '{dir_name}/{hour}_{minute}_{second}_{domain}.png'.format(
                dir_name=directory,
                hour=self.cur_time.hour,
                minute=self.cur_time.minute,
                second=self.cur_time.second,
                domain=self.domain
            )
            try:
                self.driverhandler.driver.save_screenshot(shot_path)
            except Exception:
                print "网页快照获取失败!"
            else:
                self.shot_path = shot_path

    def extractinfo(self,soup):

        tips = soup.find_all(name='a', href=True) \
               + soup.find_all(name='link', href=True) \
               + soup.find_all(name='iframe', href=True) \
               + soup.find_all(name='img', src=True) \
               + soup.find_all(name='iframe', src=True)
        for tip in tips:
            link = tip.attrs['href'] if tip.has_attr('href') else(tip.attrs['src'])
            url = self.JoinUrl(self.current_url, link)
            if self.isUnvalidUrl(url):
                continue
            new_domain = extract(url).registered_domain
            if new_domain == self.cur_domain:
                flag = 1  # 內链
            else:
                flag = 0  # 外链
                self.outer_domains.append(new_domain)
            text = self.extract_text(tip)
            if self.isImgSrc(link):
                self.img_alts.append(text)
                self.img_srcs.append(url)
            else:
                if flag == 1:
                    self.inter_urls_texts.append(text)
                    self.inter_urls.append(url)
                else:
                    self.outer_urls_texts.append(text)
                    self.outer_urls.append(url)

    def parsePageSource(self):

        try:
            page_source = self.driverhandler.driver.page_source
        except Exception,e:
            print "内容源信息获取失败!"
            return False
        else:
            try:
                soup = BeautifulSoup(page_source, 'lxml')
            except Exception,e:
                print "页面解析失败:",str(e)
            else:
                title_tip = soup.find(name='title')
                if title_tip and title_tip.string and title_tip.string.strip() != '':
                    title = title_tip.string.strip()
                    self.top_title=title
                keywords_tip = soup.find(name='meta', attrs={'name':'keywords'})
                if keywords_tip and keywords_tip.has_attr('content'):
                    self.keywords=keywords_tip.attrs['content']
                description_tip = soup.find(name='meta', attrs={'name':'description'})
                if description_tip and description_tip.has_attr('content'):
                    self.description=description_tip.attrs['content']
                self.extractinfo(soup)

            return True

    def getOtherPageSources(self):
        """
        获取页面数据
        :return: 
        """
        try:
            res = self.driverhandler.driver.find_elements_by_tag_name('iframe')
        except Exception, e:
            print 'get first iframe error:', str(e)
        else:
            if len(res) != 0:
                self.iframe_num += len(res)
                if len(res) != 1:  # 多个iframe
                    for i in range(len(res)):  # 遍历iframe
                        try:  # 切入iframe
                            self.driverhandler.driver.switch_to.frame(i)
                            page_source = self.driverhandler.driver.page_source
                            self.all_page_sources.append(page_source)
                        except Exception, e:
                            print "switch iframe error:", str(e)
                        try:  # 切回main
                            self.driverhandler.driver.switch_to.default_content()
                        except Exception, e:
                            print 'switch to default content error:', str(e)
                            break
                else:  # 单个iframe,多层
                    try:  # 切入iframe
                        self.driverhandler.driver.switch_to.frame(0)
                        page_source = self.driverhandler.driver.page_source
                        self.all_page_sources.append(page_source)
                    except Exception, e:
                        print "iframe switch error:", str(e)
                    else:
                        try:
                            res = self.driverhandler.driver.find_elements_by_tag_name('iframe')
                        except Exception, e:
                            print 'get iframe error:', str(e)
                        else:
                            if len(res) != 0:  # 多层
                                self.iframe_num += len(res)
                                for i in range(len(res)):
                                    try:
                                        self.driverhandler.driver.switch_to.frame(i)
                                        page_source = self.driverhandler.driver.page_source
                                        self.all_page_sources.append(page_source)
                                    except Exception, e:
                                        print "iframe switch error:", str(e)
                                    try:
                                        self.driverhandler.driver.switch_to.default_content()
                                        self.driverhandler.driver.switch_to.frame(0)
                                    except Exception, e:
                                        print 'switch to parent content error:', str(e)
                                        break
                        try:
                            self.driverhandler.driver.switch_to.default_content()
                        except Exception, e:
                            print 'switch to default content error:', str(e)

    def containChineseWord(self,word):

        try:
            zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')
            match = zh_pattern.search(word)
        except Exception:
            return False
        else:
            return True if match else(False)

    def isImgSrc(self,link):

        if (link.find('jpg') != -1 or link.find('jepg') != -1
            or link.find('png') != -1 or link.find('gif') != -1):
            return True
        else:
            return False

    def extract_text(self,tip):
        """
        提取标签内的文本
        :param tip: 
        :return: 
        """
        text=""
        if tip.has_attr('title') and tip.attrs['title']:
            text = tip.attrs['title'].strip()
        elif tip.has_attr('alt') and tip.attrs['alt']:
            text = tip.attrs['alt'].strip()
        elif tip.text:
                text = tip.text.strip()
        return text

    def JoinUrl(self,base_url,link):

        try:
            url = urljoin(base_url, link)
        except Exception, e:
            print "join url error:",str(e)
        else:
            return url

    def isUnvalidUrl(self,url):

        if (not url or url.find('javascript')!=-1 or
                re.search(self.filter_mode, url) or not re.search(self.url_mode, url)):
            return True
        else:
            return False

    def parseOtherPageSources(self):

        for page_source in self.all_page_sources:
            try:
                soup = BeautifulSoup(page_source, 'lxml')
            except Exception,e:
                print "内嵌页面解析失败:",str(e)
            else:
                title_tip = soup.find(name='title')
                if title_tip and title_tip.string and title_tip.string.strip() != '':
                    title = title_tip.string.strip()
                    self.titles.append(title)
                meta_tips = soup.find_all(name='meta', content=True)
                for m_tip in meta_tips:
                    mt = m_tip.attrs['content']
                    if mt is not None and mt.strip() != '' and self.containChineseWord(mt):
                        self.metas.append(mt)
                self.extractinfo(soup)

    def duplicateRemoval(self,urls,texts):

        new_urls=[]
        new_texts=[]
        for url,text in zip(urls,texts):
            if url not in new_urls:
                new_urls.append(url)
                new_texts.append(text)

        return new_urls,new_texts

    def _get_hidden_domains(self):

        texts=self.titles+self.metas+self.img_alts+self.inter_urls_texts+self.outer_urls_texts
        for text in texts:
            while len(text) != 0:
                gp = re.search(self.domain_mode, text)
                if gp and gp.group():
                    dm=gp.group()
                    hidden_domain = extract(dm).registered_domain
                    if hidden_domain != '' and hidden_domain.lower() != self.cur_domain:
                        self.hidden_domains.append(hidden_domain.lower())
                    text = text[gp.end() + 1:]
                else:
                    break
        self.hidden_domains=list(set(self.hidden_domains))
        self.outer_domains=list(set(self.hidden_domains)|set(self.outer_domains))

    def _get_urls_texts(self):

        self.outer_urls,self.outer_urls_texts=self.duplicateRemoval(self.outer_urls,self.outer_urls_texts)
        self.inter_urls, self.inter_urls_texts = self.duplicateRemoval(self.inter_urls, self.inter_urls_texts)
        self.img_srcs, self.img_alts = self.duplicateRemoval(self.img_srcs, self.img_alts)

    def main(self,item,protocol="http"):
        """
        主程序
        :param item: url/domain
        :param protocol: http/https/None
        :return: 
        """
        if protocol=="":
            self.globe_variable_initializer(extract(item).registered_domain, protocol)
            return self.get_format_result()
        if protocol and protocol not in ("http","https","ftp"):
            print "网络协议输入不合法!"
            sys.exit(-1)
        if re.search(self.url_mode,item):
            protocol=item.split(":")[0]
            url=item
            domain=extract(url).registered_domain
        elif re.search(self.domain_mode,item):#domain
            domain=item
            url='{protocol}://www.{domain}'.format(protocol=protocol,domain=domain)
        else:
            print "输入url或域名不合法!"
            sys.exit(-1)
        self.counter+=1
        print "初始化默认参数..."
        self.globe_variable_initializer(domain,protocol)
        print "打开网页..."
        flag = self.driverhandler.open_web(url)
        self.timeout_flag=flag
        print "获取状态信息..."
        self.getHttpStatus()
        if flag==1:
            self.web_status='open'
            print "获取基本信息..."
            try:
                self.current_url=self.driverhandler.driver.current_url
                self.cur_domain=extract(self.current_url).registered_domain
                if self.domain!=self.cur_domain:
                    if self.http_code and str(self.http_code)[0]=="3":
                        self.redirect = "http重定向".decode("utf8")
                    else:
                        self.redirect = "js重定向".decode("utf8")
                else:
                    self.redirect = "未重定向".decode("utf8")
                self.top_title=self.driverhandler.driver.title
            except Exception,e:
                e = str(e)
                if e.find("Alert text") != -1:
                    print "*" * 100
                    startidx = e.find("{")
                    endidx = e.find("}")
                    s = e[startidx+1:endidx]
                    self.top_title=str(s[s.find(":")+1:])
                    self.alert_flag=1
                else:
                    print "获取标题失败:", str(e)
            print "获取快照..."
            self.snapShot()
            print "获取页面文本链接信息..."
            if self.parsePageSource():
                print "获取内嵌页面文本链接信息..."
                try:
                    self.getOtherPageSources()
                    self.parseOtherPageSources()
                except Exception, e:
                    print "内嵌信息获取失败:", str(e)
            print "整合链接信息..."
            self._get_hidden_domains()
            self._get_urls_texts()
        else:
            self.web_status='closed'
        if flag==0 or self.counter%self.period==0:#防止内存饱和
            print "重启浏览器..."
            self.driverhandler.destory_driver()
            self.driverhandler.create_driver()
            print "重启已浏览器!"
        self.cur_time = datetime.now()
        print "页面信息提取完毕!"
        return self.get_format_result()

    def get_format_result(self):
        """
        获取格式化输出结果
        :return: 
        """
        result_dict={
            'domain':self.domain,
            'cur_ip':self.cur_ip,
            'cur_port':self.cur_port,
            'boswer_log':self.bowser_log,
            'web_status': self.web_status,
            'timeout_flag': self.timeout_flag,
            'cur_domain':self.cur_domain,
            'current_url':self.current_url,
            'http_code':self.http_code,
            'redirect':self.redirect,
            'protocol':self.protocol,
            'shot_path': self.shot_path,
            'alert_flag':self.alert_flag,
            'iframe_num':self.iframe_num,
            'inter_urls':self.inter_urls,
            'outer_urls':self.outer_urls,
            'img_srcs':self.img_srcs,
            'inter_urls_texts':self.inter_urls_texts,
            'outer_urls_texts':self.outer_urls_texts,
            'img_alts':self.img_alts,
            'hidden_domains':self.hidden_domains,
            'outer_domains':self.outer_domains,
            'top_title':str(self.top_title),
            'keywords':self.keywords,
            'description':self.description,
            'titles':self.titles,
            'metas':self.metas,
            'cur_time':self.cur_time
        }

        return result_dict

    def print_result(self):

        print "当前域名:",str(self.domain)
        print "访问时间:",str(self.cur_time)
        print "当前IP:当前端口=>{ip}:{port}".format(ip=self.cur_ip,port=self.cur_port)
        print "网站开放情况:",self.web_status
        print "页面加载超时情况:",("超时") if self.timeout_flag else("未超时")
        print "访问网址:",self.current_url
        print "访问主机:",self.cur_domain
        print "状态码",self.http_code
        print "重定向情况:",self.redirect
        print "快照存放路径",self.shot_path
        print "弹出框情况:",("有弹出") if self.alert_flag else("没有弹出")
        print "使用iframe框架数:",str(self.iframe_num)
        print "网站标题:",str(self.top_title)
        print "网站关键词:",self.keywords
        print "网站描述:",self.description
        print "内嵌标题:",'/'.join(self.titles)
        print "内嵌元信息:",'/'.join(self.metas)
        print "內链数:",str(len(self.inter_urls))
        print "外链数:",str(len(self.outer_urls))
        print "图片数:",str(len(self.img_srcs))
        print "暗链数:",str(len(self.hidden_domains))
        print "链出域名数:",str(len(self.outer_domains))
        print "*"*10+"锚/锚文本"+"*"*10
        for url,text in zip(self.inter_urls,self.inter_urls_texts):
            print '{0}:{1}'.format(text,url)
        for url,text in zip(self.outer_urls,self.outer_urls_texts):
            print '{0}:{1}'.format(text,url)
        for src,alt in zip(self.img_srcs,self.img_alts):
            print '{0}:{1}'.format(alt,src)
        print "*" * 10 + "锚/锚文本" + "*" * 10
        print "*" * 10 + "暗链" + "*" * 10
        print '/'.join(self.hidden_domains)
        print "*" * 10 + "链出域名" + "*" * 10
        print '/'.join(self.outer_domains)

def exper(item,driver_type='chrome'):
    """
    '137133.com'
    closed_period=50,shot_dirname='shot_files',max_time=60,wait_time=3,ban_image=False,headless=False
    :param item: 
    :return: 
    """
    paras_dict=dict(
        closed_period=50,
        shot_dirname='shot_files',
        max_time=60,
        wait_time=3,
        ban_image=True,
        headless=True
    )
    wis=WebInfoSpider(driver_type,**paras_dict)
    wis.main(item)
    wis.print_result()
    wis.driverhandler.destory_driver()

if __name__ == "__main__":
    # exper('509mm.com')#'0b33.com''00000e.com''138429.com','00000e.com'
    exper('00000e.com')
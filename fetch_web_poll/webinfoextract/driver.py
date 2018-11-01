#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

"""

import os
import sys
import time
import commands
from settings import DRIVER_SETTINGS
from selenium import webdriver
from selenium.webdriver.common import desired_capabilities

class DriverHandler(object):
    """
    driverhandler:无界面web驱动柄
    """
    def __init__(self,drivertype,*args,**kwargs):
        """
        最长加载时间max_time
        等待时间wait_time
        图片是否加载ban_image true/false
        是否关闭浏览器界面headless true/false
        :param drivertype: 浏览器驱动 chrome/phantomjs
        :param kwargs: 
        """
        if drivertype not in("chrome","phantomjs"):
            print "无此浏览驱动,请选择chrome/phantomjs!"
            sys.exit(-1)
        self.driver_type=drivertype
        driver_path_name='{drivername}_path'.format(drivername=drivertype)
        self.driver_path = DRIVER_SETTINGS[driver_path_name]
        self.max_time=self.set_default(kwargs,'max_time',10)
        self.wait_time=self.set_default(kwargs,'wait_time',1)
        self.ban_image=self.set_default(kwargs,'ban_image',False)
        self.headless= self.set_default(kwargs,'headless',False)
        self.create_driver()

    def create_driver(self):
        """
        创建驱动柄
        :param timeout: 
        :return: 
        """
        dcap = desired_capabilities.DesiredCapabilities
        if self.driver_type=="phantomjs":
            dcapp = dcap.PHANTOMJS
            dcapp["phantomjs.page.settings.loadImages"] = not self.ban_image
            self.driver = webdriver.PhantomJS(
                executable_path=self.driver_path,
                desired_capabilities=dcapp
            )
        else:
            dcapp = dcap.CHROME
            dcapp['loggingPrefs'] = {'performance': 'ALL'}
            chromeOptions = webdriver.ChromeOptions()
            if self.headless:
                os.environ["webdriver.chrome.driver"] = self.driver_path
                chromeOptions.add_argument('--headless')
            #1:允许所有图片；2：阻止所有图片；3：阻止第三方服务器图片
            images_flag=1 if not self.ban_image else(2)
            prefs = {
                "profile.managed_default_content_settings": {
                    'images': images_flag
                }
            }
            chromeOptions.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome(
                executable_path=self.driver_path,
                chrome_options=chromeOptions,
                desired_capabilities=dcapp
            )
        self.driver.set_page_load_timeout(self.max_time)
        self.driver.set_script_timeout(self.max_time)

    def destory_driver(self):
        """
        关闭/销毁驱动
        :return: 
        """
        try:
            self.driver.quit()
        except Exception,e:
            print "浏览器关闭失败:",str(e)
            cur_pid = os.getpid()
            cmd = 'ps -efw|grep {driver_type}|grep -v grep|cut -c 9-15,16-21' \
                  ''.format(driver_type=self.driver_type)
            output = commands.getoutput(cmd)
            lines = output.split('\n')
            pid_list = []
            for line in lines:
                tup = tuple([item.strip() for item in line.split(' ') if item.strip() != ''])
                pid, ppid = tup
                if ppid == str(cur_pid):
                    print "kill " + str(pid)
                    pid_list.append(pid)
            pids = ' '.join(pid_list)
            commands.getoutput('kill -9 ' + pids)
            print "命令行清除浏览器进程完毕!"

    def open_web(self,url):
        """
        打开页面
        :param url: 
        :return: 
        """
        try:
            self.driver.get(url)
            time.sleep(self.wait_time)
        except Exception,e:
            if str(e).find('timeout')!=-1:
                print "加载超时!"
                return -1#超时
            else:
                print "加载异常!"
                return 0#异常
        else:
            return 1#正常

    def set_default(self,paras_dict, key,default):

        return default if key not in paras_dict else(paras_dict[key])
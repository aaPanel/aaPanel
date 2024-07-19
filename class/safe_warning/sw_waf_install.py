#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检测风险用户
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'WAF firewall detection'
_version = 1.0                              # 版本
_ps = "Detect whether a WAF firewall is installed"               # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_waf_install.pl")
_tips = [
    "It is recommended to install a WAF firewall, such as: Pagoda Nginx Firewall, Pagoda Apache Firewall, Nginx Free Firewall, etc.",
    "Note: Only one type of WAF firewall can be installed. Installing too many WAF firewalls may cause your website to be abnormal and increase unnecessary server overhead"
    ]

_help = ''
_remind = "WAF firewall is the first line of defense to protect the server, can block external network attacks, to ensure the safe and stable operation of the website. "

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    web_list = [
        '/www/server/nginx/sbin/nginx',
        '/www/server/apache/bin/httpd',
        '/usr/local/lsws/bin'
        ]
    is_install_web = False
    for w in web_list:
        if os.path.exists(w):
            is_install_web = True
            break

    if not is_install_web:
        return True,'Risk-free'

    waf_list = [
        '/www/server/panel/plugin/btwaf/info.json',
        '/www/server/panel/plugin/btwaf_httpd/info.json',
        '/www/server/panel/plugin/free_waf/info.json',
        '/usr/local/yunsuo_agent/uninstall',
        '/etc/safedog',
        '/usr/share/xmirror/scripts/uninstall.sh'
        ]

    for waf in waf_list:
        if os.path.exists(waf):
            return True,'Risk-free'

    return True,'If the WAF firewall is not installed, the server website is vulnerable to attacks and there is a security risk'


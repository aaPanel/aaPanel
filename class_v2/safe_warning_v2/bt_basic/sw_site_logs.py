#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 网站日志检测
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'Web log detection'
_version = 1.0                              # 版本
_ps = "Check all site log retention cycles for compliance"          # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_site_logs.pl")
_tips = [
    "In the [Scheduled Task] page, set the log cutting of the specified website or all websites once a day and save more than 180 copies ",
    "Tip: According to Article 21 of the Network Security Law, network logs should be retained for no less than six months."
    ]

_help = ''
_remind = 'This solution can help discover the risk of external intrusions and vulnerabilities by retaining logs to ensure the security of your website. Make sure you have enough log space. '


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    if public.M('crontab').where('sType=? AND sName=? AND save>=?',('logs','ALL',180)).count():
        return True,'Risk-free'

    log_list = public.M('crontab').where('sType=? AND save<?',('logs',180)).field('sName').select()

    not_logs = []
    for ml in log_list:
        if ml['sName'] in not_logs: continue
        not_logs.append(ml['sName'])

    #如果有设置切割所有网站日志,且设置不合规
    if 'ALL' in not_logs:
        log_list = public.M('crontab').where('sType=? AND save>=?',('logs',180)).field('sName').select()
        ok_logs = []
        for ml in log_list:
            if ml['sName'] in ok_logs: continue
            ok_logs.append(ml['sName'])

        not_logs = []
        site_list = public.M('sites').field('name').select()
        for s in site_list:
            if s['name'] in ok_logs: continue
            if s['name'] in not_logs: continue
            not_logs.append(s['name'])

    if not_logs:
        return False ,'The following website log preservation cycle is not compliant: <br />' + ('<br />'.join(not_logs))

    return True,'Risk-free'



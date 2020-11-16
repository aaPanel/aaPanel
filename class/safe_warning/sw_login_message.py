#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检测用户登录通知
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'SSH user login notification'
_version = 1.0                              # 版本
_ps = "Check whether SSH user login notification is enabled"              # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_login_message.pl")
_tips = [
    "On the [Security] page, [SSH security management] - [login alarm] enable the [monitor root login] function"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    data = public.ReadFile('/etc/bashrc')
    if not data: return True,'Risk-free'
    if re.search('python /www/server/panel/class/ssh_security.py login', data):
        return True,'Risk-free'
    else:
        return False,'SSH user login notification is not configured, so it is impossible to know whether the server has been illegally logged in in the first place'
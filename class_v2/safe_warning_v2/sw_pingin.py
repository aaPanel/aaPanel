#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检测是否禁ping
# -------------------------------------------------------------------


import os,sys,re,public

_title = '2222222'
_version = 1.0                              # 版本
_ps = "222222222(禁Ping)"              # 描述
_level = 0                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ping_in.pl")
_tips = [
    "Enable Disable Ping in Security page ",
    "Note: You cannot ping the server IP or domain name after opening, please set it according to your actual needs"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    try:
        cfile = '/proc/sys/net/ipv4/icmp_echo_ignore_all'
        conf = public.readFile(cfile)
        if conf:
            if int(conf)!=1:
                return False,'The "Ban Ping" function is not enabled at present, there is a risk that the server is attacked by ICMP or swept'
        else:
            return True,"Risk-free"
    except:
        return True,"Risk-free"
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
# 检测是否禁ping
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'ICMP detection'
_version = 1.0                              # 版本
_ps = "Check whether ICMP access is allowed (Block ICMP)"              # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ping.pl")
_tips = [
    "Turn on the [Block ICMP] function in the [Security] page",
    "Note: The server IP or domain name cannot be Ping after it is turned on, please set according to actual needs"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    
    cfile = '/etc/sysctl.conf'
    conf = public.readFile(cfile)
    rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
    tmp = re.search(rep,conf)
    if tmp:
        if tmp.groups(0)[0] == '1':
            return True,'Rick-free'

    return False,'If the [Block ICMP] function is not enabled, there is a risk that the server will be attacked or scanned by ICMP'

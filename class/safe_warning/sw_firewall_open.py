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
# 系统防火墙检测
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'System firewall'
_version = 1.0                              # 版本
_ps = "Check whether the system firewall is enable"               # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_firewall_open.pl")
_tips = [
    "It is recommended to enable the system firewall to prevent all server ports from being exposed to the Internet. If the server has [security group] function, please ignore this prompt",
    "Note: To open the system firewall, the ports that need to be opened, especially SSH and panel ports, should be added to the release list in advance, otherwise the server may not be able to access them"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''
    
    if os.path.exists('/usr/sbin/firewalld'): 
        if public.ExecShell("systemctl status firewalld|grep 'active (running)'")[0]:
            return True,'Risk-free'

    elif os.path.exists('/usr/sbin/ufw'): 
        if public.ExecShell("ufw status|grep 'Status: active'")[0]:
            return True,'Risk-free'
    else:
        if public.ExecShell("service iptables status|grep 'Table: filter'")[0]:
            return True,'Risk-free'
    
    return False,'The system firewall is not opened, and there is a security risk'
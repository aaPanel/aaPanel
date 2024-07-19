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
_remind = 'This solution can reduce the risk surface of the server exposure and enhance the protection of the website. However, you need to add the port that needs to be opened at the port rule, otherwise the website will be unreachable. '
def check_run():
    '''
        @name 开始检测
        @author hwliang<2022-08-18>
        @return tuple (status<bool>,msg<string>)
    '''
    status = public.get_firewall_status()
    if status == 1:
        return True,'Risk-free'
    elif status == -1:
        return False,'System firewall is not installed, there are security risks'
    else:
        return False,'System firewall is not installed, there are security risks'
#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检查SSH root是否可以登录
# -------------------------------------------------------------------
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os, sys, re, public

_title = 'Check if SSH root can log in'
_version = 1.0  # 版本
_ps = "Check if SSH root can log in"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_root.pl")
_tips = [
    "Add [ PermitRootLogin no ] parameter in [/etc/ssh/sshd_config]",
    "PermitRootLogin no",
]
_help = ''
_remind = 'SSH remote login as root is not possible after this solution is fixed'


def check_run():
    #ssh 检查root 登录
    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data = public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search(r'PermitRootLogin\s+no', info_data):
                    return True, 'Risk-free'
                else:
                    return True, 'Risk-free'
                    return False, 'The parameter [PermitRootLogin] in /etc/ssh/sshd_config is configured as: "yes", please set it to "no"'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'
#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# SSH过期提前警告天数
# -------------------------------------------------------------------



# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import re,public,os

_title = 'SSH Expiration Warning Days'
_version = 1.0                              # 版本
_ps = "SSH expiration warning days"          # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_passwarn.pl")
_tips = [
    "Set PASS_WARN_AGE to 7 or greater in 【/etc/login.defs】",
    "Example: PASS_WARN_AGE 30. Also execute the command to apply settings to the root user: chage --warndays 7 root",
    ]

_help = ''
_remind = 'This setting determines how many days before password expiration a warning will be issued, preventing forgotten passwords from affecting server process execution. Note that this reminder only appears upon logging into the server; it is recommended to set up alert methods in the panel’s notification settings.'


def check_run():
    '''
        @name SSH过期提前警告天数
        @time 2022-08-10
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    if os.path.exists('/etc/login.defs'):
        try:
            info_data=public.ReadFile('/etc/login.defs')
            if info_data:
                if re.search(r'PASS_WARN_AGE\s+(-?\d+)',info_data):

                    passwarnage=re.findall(r'PASS_WARN_AGE\s+(-?\d+)',info_data)[0]
                    #passwarnage 需要大于等于7
                    if int(passwarnage) >= 7:
                        return True,'No risk'
                    else:
                        return False,'Current PASS_WARN_AGE is: '+passwarnage+', please set it to 7 or greater'
                else:
                    return True,'No risk'
        except:
            return True,'No risk'
    return True,'No risk'

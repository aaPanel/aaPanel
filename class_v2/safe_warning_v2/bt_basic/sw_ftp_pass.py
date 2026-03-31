#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: linxiao
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# FTP弱口令检测
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os,public

_title = 'Weak password detection for FTP services'
_version = 2.0  # 版本
_ps = "Detect enabled weak passwords for FTP services"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-12'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_pass.pl")
_tips = [
    "Please go to [FTP] page to change the FTP password ",
    "Note: Please do not use too simple account password, so as not to cause security risks ",
    "Strong passwords are recommended: numeric, upper - and lowercase, special characters, and no less than seven characters long." ,
    "Using [Fail2ban] plugin to protect FTP server"
]

_help = ''
_remind = 'This scheme can strengthen the protection of the FTP server, to prevent intruders from blasting into the FTP server. '


def check_run():
    """检测FTP弱口令
        @author linxiao<2020-9-19>
        @return (bool, msg)
    """

    pass_info = public.ReadFile("/www/server/panel/config/weak_pass.txt")
    if not pass_info: return True, 'Risk-free'
    pass_list = pass_info.split('\n')
    data = public.M("ftps").select()
    ret = ""
    for i in data:
        if i['password'] in pass_list:
            ret += "FTP：" + i['name'] + "weak passwords exist：" + i['password'] + "\n"
    if ret:
        # print(ret)
        return False, ret
    else:
        return True, 'Risk-free'

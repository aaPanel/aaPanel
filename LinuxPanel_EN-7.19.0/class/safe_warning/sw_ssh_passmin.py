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
# 检查SSH密码失效时间
# -------------------------------------------------------------------
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os, sys, re, public

_title = 'Check minimum interval between SSH password changes'
_version = 1.0  # 版本
_ps = "Check minimum interval between SSH password changes"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_passmin.pl")
_tips = [
    "[/etc/login.defs] PASS_MIN_DAYS should be set to be greater than or equal to 7",
    "PASS_MIN_DAYS 7 needs to execute the command at the same time to set the expiration time of the root password. The command is as follows: chage --mindays 7 root",
]
_help = ''
_remind = 'This solution sets the number of days after the SSH login password is changed, it cannot be changed again. '

def check_run():
    try:
        p_file = '/etc/login.defs'
        p_body = public.readFile(p_file)
        if not p_body: return True, 'Risk-free'
        tmp = re.findall("\nPASS_MIN_DAYS\\s+(.+)", p_body, re.M)
        if not tmp: return True, 'Risk-free'
        maxdays = tmp[0].strip()
        #7-14
        if int(maxdays) < 7:
            return False, '【%s】In the file, PASS_MIN_DAYS is greater than or equal to 7' % p_file
        return True, 'Risk-free'
    except:
        return True, 'Risk-free'

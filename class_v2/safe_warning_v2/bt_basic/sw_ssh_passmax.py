#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检查SSH密码失效时间
# -------------------------------------------------------------------
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os, sys, re, public

_title = 'Check SSH password expiration time'
_version = 1.0  # 版本
_ps = "Check SSH password expiration time"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_passmax.pl")
_tips = [
    "[/etc/login.defs] Use a non-password login key pair. Please ignore this, and set the PASS_MAX_DAYS parameter to between 90-180 in /etc/login.defs",
    "PASS_MAX_DAYS 90 You need to execute the command to set the root password expiration time at the same time. The command is as follows: chage --maxdays 90 root",
]
_help = ''
_remind = 'This solution reduces the risk of a breach by setting an expiration date for the root login password. Note that the repair scheme will invalidate the root password after the expiration date, so it is necessary to modify the password before the expiration date. If the modification is not timely, it may affect the operation of some services. '

def check_run():
    try:
        p_file = '/etc/login.defs'
        p_body = public.readFile(p_file)
        if not p_body: return True, 'Risk-free'
        tmp = re.findall("\nPASS_MAX_DAYS\\s+(.+)", p_body, re.M)
        if not tmp: return True, 'Risk-free'
        maxdays = tmp[0].strip()
        #60-180之间
        if int(maxdays) < 90 or int(maxdays) > 180:
            return False, '【%s】Set PASS_MAX_DAYS to between 90-180 in the file' % p_file
        return True, 'Risk-free'
    except:
        return True, 'Risk-free'


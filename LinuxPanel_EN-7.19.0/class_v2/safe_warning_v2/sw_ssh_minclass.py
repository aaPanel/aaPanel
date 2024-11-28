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
# SSH密码复杂度检查
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = 'SSH password complexity check'
_version = 1.0  # 版本
_ps = "SSH password complexity check"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_minclass.pl")
_tips = [
    "【/etc/security/pwquality.conf】 Set password complexity to require 3 or 4 types of characters, such as lowercase letters, uppercase letters, numbers, and special characters. like：",
    "minclass=3",
]
_help = ''
_remind = 'This scheme strengthens the complexity of the server login password and reduces the risk of being successfully exploded. '

def check_run():
    try:
        p_file = '/etc/security/pwquality.conf'
        p_body = public.readFile(p_file)
        if not p_body: return True, 'Risk-free'
        tmp = re.findall(r"\s*minclass\s+=\s+(.+)", p_body, re.M)
        if not tmp: return True, 'Risk-free'
        minlen = tmp[0].strip()
        if int(minlen) <3:
            return False, '【%s】set the minclass setting to 3 or 4 in the file' % p_file
        return True, 'Risk-free'
    except:
        return True, 'Risk-free'

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
# SSH密码复杂度检查
# -------------------------------------------------------------------
import sys,os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os,sys,re,public

_title = 'SSH password length check'
_version = 1.0                              # 版本
_ps = "SSH password length check"                      # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_security.pl")
_tips = [
    "In the [/etc/security/pwquality.conf] file, set minlen (minimum password length) to 9-32 bits",
    "minlen=9",
    ]
_help = ''
_remind = 'This solution enforces a minimum login password length, reducing the risk of server blow-up. '


def check_run():
   try:
        p_file = '/etc/security/pwquality.conf'
        p_body = public.readFile(p_file)
        if not p_body: return True, 'Risk-free'
        tmp = re.findall(r"\s*minlen\s+=\s+(.+)", p_body, re.M)
        if not tmp: return True, 'Risk-free'
        minlen = tmp[0].strip()
        if int(minlen) < 9:
            return False, 'In the [%s] file, set minlen (minimum password length) to 9-32 characters'%p_file

        return True, 'Risk-free'
   except:
        return True, 'Risk-free'

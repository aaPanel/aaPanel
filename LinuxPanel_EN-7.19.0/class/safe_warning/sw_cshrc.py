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
# 用户缺省权限检查
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = '[/etc/csh.cshrc] User default permission check'
_version = 1.0  # 版本
_ps = "[/etc/csh.cshrc] User default permission check"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cshrc.pl")
_tips = [
    "[/etc/csh.cshrc] The umask set in the file is 002, which does not meet the requirements. It is recommended to set it to 027",
    "The operation is as follows: Modify umask to 027",
]
_help = ''
_remind = 'This scheme can strengthen the protection of user privileges on the system. '

def check_run():
      # 判断是否存在/etc/profile文件
    if os.path.exists("/etc/csh.cshrc"):
        # 读取文件内容
        profile = public.ReadFile("/etc/csh.cshrc")
        # 判断是否存在umask设置
        if re.search("umask 0",profile):
            # 判断是否设置为027
            if re.search("umask 027",profile):
                return True,"Risk-free"
            else:
                # return False,"umask not set to 027"
                return True, "Risk-free"
        else:
            # return False,"umask not set"
            return True, "Risk-free"
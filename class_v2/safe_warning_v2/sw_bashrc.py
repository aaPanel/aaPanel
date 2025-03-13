#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 用户缺省权限检查
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = '[/etc/bashrc] User default permission check'
_version = 1.0  # 版本
_ps = "/etc/bashrc User default permission check"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_bashrc.pl")
_tips = [
    "[/etc/bashrc] The umask set in the file is 002, and it is recommended to set it to 027",
    "Solution: Modify the /etc/bashrc file permission to 027",
]
_help = ''
_remind = 'This scheme can strengthen the protection of system user rights, but it may affect the original operation habits.'


def check_run():
      # 判断是否存在/etc/profile文件
    if os.path.exists("/etc/bashrc"):
        # 读取文件内容
        profile = public.ReadFile("/etc/bashrc")
        # 判断是否存在umask设置
        if re.search("umask 0",profile):
            # 判断是否设置为027
            if re.search("umask 027",profile):
                return True,"Risk-free"
            else:
                return False,"umask is not set to 027"
        else:
            return False,"umask not set"
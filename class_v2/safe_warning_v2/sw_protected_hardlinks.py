#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 开启地址空间布局随机化
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = 'Whether hard link protection is enabled'
_version = 1.0  # 版本
_ps = "Whether hard link protection is enabled"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_protected_hardlinks.pl")
_tips = [
    "operation is as follows: sysctl -w fs.protected_hardlinks=1",
]
_help = ''
_remind = "By enabling this kernel parameter, users can no longer create soft or hard links to files they do not own, which reduces the vulnerability of privileged programs to access insecure filesystems and enhances server security."


def check_run():
    try:
        if os.path.exists("/proc/sys/fs/protected_hardlinks"):
            protected_hardlinks = public.ReadFile("/proc/sys/fs/protected_hardlinks")
            if int(protected_hardlinks) != 1:
                return False, 'Hard link protection is not enabled'
            else:
                return True, "Risk-free"
    except:
        return True, "Risk-free"
    return True, "Risk-free"

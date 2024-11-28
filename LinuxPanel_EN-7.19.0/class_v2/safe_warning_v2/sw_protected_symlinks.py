#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 开启软链接保护
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = 'Whether to enable soft link protection'
_version = 1.0  # 版本
_ps = "Whether to enable soft link protection"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_protected_symlinks.pl")
_tips = [
    "operation is as follows: sysctl -w fs.protected_symlinks=1",
]
_help = ''
_remind = "By enabling this kernel parameter, symbolic links are only allowed to be tracked if they are outside the sticky global writable directory, or if the directory owner matches the owner of the symbolic link. Banning such symbolic links helps mitigate vulnerabilities in insecure file systems based on privileged program access."


def check_run():
    try:
        if os.path.exists("/proc/sys/fs/protected_symlinks"):
            protected_symlinks = public.ReadFile("/proc/sys/fs/protected_symlinks")
            if int(protected_symlinks) != 1:
                return False, 'Soft link protection is not enabled'
            else:
                return True, "Risk-free"
    except:
        return True, "Risk-free"
    return True, "Risk-free"

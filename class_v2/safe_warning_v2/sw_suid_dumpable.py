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

_title = 'Whether core dumps are restricted'
_version = 1.0  # 版本
_ps = "Whether core dumps are restricted"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-22'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_suid_dumpable.pl")
_tips = [
    "operation is as follows: sysctl -w fs.suid_dumpable=0",
]
_help = ''
_remind = 'Core dumps of setuid programs are more likely to contain sensitive data, and limiting the ability of any setuid program to write to core files reduces the risk of sensitive data leakage.'


def check_run():
    try:
        if os.path.exists("/proc/sys/fs/suid_dumpable"):
            suid_dumpable = public.ReadFile("/proc/sys/fs/suid_dumpable")
            if int(suid_dumpable) != 0:
                return False, 'The core dump is not limited, and information leakage may occur.'
            else:
                return True, "Risk-free"
    except:
        return True, "Risk-free"
    return True, "Risk-free"

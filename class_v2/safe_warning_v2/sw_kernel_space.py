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
# 开启地址空间布局随机化
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = 'Enable kernel.randomize_va_space'
_version = 1.0  # 版本
_ps = "Enable kernel.randomize_va_space"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_kernel_space.pl")
_tips = [
    "[/proc/sys/kernel/randomize_va_space] value is 2: ",
    "How to set：sysctl -w kernel.randomize_va_space=2",
]
_help = ''
_remind = 'This scheme can reduce the risk of intrusers using buffer overflow to attack the server, and strengthen the protection of the server. '
def check_run():
       try:
           if os.path.exists("/proc/sys/kernel/randomize_va_space"):
               randomize_va_space=public.ReadFile("/proc/sys/kernel/randomize_va_space")
               if int(randomize_va_space)!=2:
                   return False, 'Enable kernel.randomize_va_space'
               else:
                   return True,"Risk-free"
       except:
           return True, "Risk-free"
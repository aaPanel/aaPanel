#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检测是否开debug模式
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'Developer Mode'
_version = 1.0                              # 版本
_ps = "Checks whether panel developer mode is enabled"              # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_debug_mode.pl")
_tips = [
    "Turn off developer mode on the [ Settings ] page",
    "Note: Developer mode is only used for panel plug-in or API development, do not use in production environment"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    if os.path.exists('/www/server/panel/data/debug.pl'):
        return False,'[Developer mode] has been opened, and risks such as data communication and information leakage exist'
    return True,'Risk-free'

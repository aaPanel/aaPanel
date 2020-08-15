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
# 面板端口检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Panel port'
_version = 1.0                              # 版本
_ps = "Check whether the current panel port is safe"      # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-03'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_port.pl")
_tips = [
    "Please modify the default panel port on the [Settings] page",
    "Note: Servers with [Security Group] should release the new port in the [Security Group] in advance to prevent the new port cannot be opened"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    port_file = '/www/server/panel/data/port.pl'
    port = public.readFile(port_file)
    if not port: return True,'Rick-free'
    port = int(port)
    if port != 8888:
        return True,'Rick-free'
    return False,'The panel port is the default port ({}), which may cause unnecessary security risks'.format(port)
    

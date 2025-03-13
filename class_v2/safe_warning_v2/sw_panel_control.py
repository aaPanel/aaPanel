#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# Mysql 弱口令检测
# -------------------------------------------------------------------

import  public, os
_title = 'The panel is not monitoring'
_version = 1.0  # 版本
_ps = "The panel is not monitoring"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_control.pl")
_tips = [
    "Open it in [Monitor] - [System Monitor]"
]
_help = ''
_remind = 'Enable server monitoring, you can record the recent operation of the server, to facilitate the troubleshooting of system anomalies. '
def check_run():
    '''
        @name 面板未开启监控
        @time 2022-08-12
        @author lkq@bt.cn
    '''
    global _tips
    send_type = ""
    if os.path.exists("/www/server/panel/data/control.conf"):
        return True, 'Risk-free'
    return False, _tips[0]




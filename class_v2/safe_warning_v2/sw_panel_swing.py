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
_title = 'Panel login alarm'
_version = 1.0  # 版本
_ps = "Panel login alarm"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_swing.pl")
_tips = [
    "Enable it in [Settings] - [Security]"
]
_help = ''
_remind = 'This solution can strengthen the panel protection and reduce the risk of the panel being attacked. '
def check_run():
    '''
        @name 面板登录告警是否开启
        @time 2022-08-12
        @author lkq@bt.cn
    '''
    send_type = ""
    tip_files = ['panel_login_send.pl','login_send_type.pl','login_send_mail.pl','login_send_dingding.pl']
    for fname in tip_files:
        filename = 'data/' + fname
        if os.path.exists(filename):
            return True, 'Risk-free'
    return False, 'Please enable it in [Settings] - [Security]'




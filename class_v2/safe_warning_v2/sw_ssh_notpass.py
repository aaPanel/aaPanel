#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# 禁止SSH空密码登录
# -------------------------------------------------------------------
import re,public,os


_title = 'Prohibit SSH login with empty password'
_version = 1.0                              # 版本
_ps = "Prohibit SSH login with empty password"          # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_notpasswd.pl")
_tips = [
    "Set [PermitEmptyPasswords] in the [/etc/ssh/sshd_config] file to configure it to no",
    "Tips: Set [PermitEmptyPasswords] in the [/etc/ssh/sshd_config] file to configure it to no"
    ]

_help = ''
_remind = 'This scheme prevents the server from logging in with an empty password. Note that the server cannot login with an empty password after the repair. Ensure that the login password is configured synchronously for related business access. '


def check_run():
    '''
        @name 检测禁止SSH空密码登录
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data = public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search('\nPermitEmptyPasswords\\s*yes', info_data):
                    return False, 'The [PermitEmptyPasswords] value is: yes, please set it to no'
                else:
                    return True, 'Rick-free'
        except:
            return True, 'Rick-free'
    return True, 'Rick-free'
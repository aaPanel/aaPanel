#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh
# -------------------------------------------------------------------
# Time: 2023-11-22
# -------------------------------------------------------------------
# SSH 登录超时时间
# -------------------------------------------------------------------

import re, public, os

_title = 'SSH Login timeout configuration detection'
_version = 1.0  # 版本
_ps = "SSH Login timeout configuration detection"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_login_grace.pl")
_tips = [
    "Set [LoginGraceTime] to 60 in [/etc/ssh/sshd_config] file",
]

_help = ''
_remind = 'Setting the LoginGraceTime parameter to a small number minimizes the risk of a successful brute force attack on the SSH server. It will also limit the number of concurrent unauthenticated connections. '


def check_run():
    '''
        @name SSH 登录超时配置检测
        @author lwh<2023-11-22>
        @return tuple (status<bool>,msg<string>)
    '''
    path = '/etc/ssh/sshd_config'
    if os.path.exists(path):
        try:
            output, err = public.ExecShell(r"grep -P '^(?!#)[\s]*LoginGraceTime.*$' {}".format(path))
            if output == '' and err == '':
                return False, 'The SSH login timeout configuration is not enabled'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'

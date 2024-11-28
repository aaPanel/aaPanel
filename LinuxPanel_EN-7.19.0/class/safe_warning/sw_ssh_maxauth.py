#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@aapanel.com>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# SSH 最大连接数检测
# -------------------------------------------------------------------

import re, public, os

_title = 'SSH connection attempts'
_version = 1.0  # 版本
_ps = "SSH connection attempts"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_maxauth.pl")
_tips = [
    "Set [MaxAuthTries] to 3-5 in the [/etc/ssh/sshd_config] file",
    "Tips: Set [MaxAuthTries] to 3-5 in the [/etc/ssh/sshd_config] file"
]

_help = ''
_remind = 'This reduces the risk of server intrusion by reducing the maximum number of SSH connections. Note Before fixing, confirm the number of simultaneous connections that SSH needs to support to prevent affecting normal business operations. '


def check_run():
    '''
        @name 检测ssh最大连接数
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data = public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search(r'MaxAuthTries\s+\d+', info_data):
                    maxauth = re.findall(r'MaxAuthTries\s+\d+', info_data)[0]
                    # max 需要大于3 小于6
                    if int(maxauth.split(' ')[1]) >= 3 and int(maxauth.split(' ')[1]) <= 6:
                        return True, 'Rick-free'
                    else:
                        return False, 'The current maximum number of SSH connections is: ' + maxauth.split(' ')[1] + ', please set it to 3-5'
                else:
                    return True, 'Rick-free'
        except:
            return True, 'Rick-free'
    return True, 'Rick-free'


def repaired():
    '''
        @name 修复ssh最大连接数
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    # 暂时不处理
    pass

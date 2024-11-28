#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 开启地址空间布局随机化
# -------------------------------------------------------------------
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os, sys, re, public

_title = 'Critical file permission checks'
_version = 1.0  # 版本
_ps = "Critical file permission checks"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_file_mod.pl")
_tips = [
    "On the [File] page, set the correct permissions and owner for the specified directory or file",
]
_help = ''

def check_run():
    dir_list = [
        ['/etc/shadow', 400, 'root'],
        ['/etc/security', 600, 'root'],
        ['/etc/passwd', 644, 'root'],
        ['/etc/services', 644, 'root'],
        ['/etc/group', 644, 'root'],
        ['/var/spool/cron/root',600, 'root'],
        ['/etc/ssh/sshd_config',644,'root'],
        ['/etc/sysctl.conf',644,'root'],
        ['/etc/crontab',644,'root'],
        ['/etc/hosts.deny',644,'root'],
        ['/etc/hosts.allow',644,'root'],
        ['/etc/gshadow',400,'root'],
        ['/etc/passwd',644,'root'],
        ['/etc/shadow',400,'root'],
        ['/etc/group',644,'root'],
        ['/etc/gshadow',400,'root'],
        ]

    not_mode_list = []

    for d in dir_list:
        if not os.path.exists(d[0]): continue
        u_mode = public.get_mode_and_user(d[0])
        if u_mode['user'] != d[2]:
            not_mode_list.append("{} Current permissions: {} : {} Suggested changes to: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
        if int(u_mode['mode']) != d[1]:
            not_mode_list.append("{} Current permissions: {} : {} Suggested changes to: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))

    if not_mode_list:
        return False,'The following critical files or directories have permission errors: <br />' + ("<br />".join(not_mode_list))
    else:
        return True,"Risk-free"


# check_run()
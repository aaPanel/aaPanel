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
# 检测关键目录权限是否正确
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'System directory permissions'
_version = 1.0                              # 版本
_ps = "Checks if the System directory permissions are correct"              # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_dir_mode.pl")
_tips = [
    "On the [ File ] page, set the correct permissions and owner for the specified directory or file",
    "Note 1: When setting directory permissions through the [File] page, please cancel the [Apply to subdirectories] option",
    "Note 2: Incorrect file permissions not only pose a security risk, but also may cause some software on the server to fail to work properly"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    dir_list = [
        ['/usr',755,'root'],
        ['/usr/bin',555,'root'],
        ['/usr/sbin',555,'root'],
        ['/usr/lib',555,'root'],
        ['/usr/lib64',555,'root'],
        ['/usr/local',755,'root'],
        ['/etc',755,'root'],
        ['/etc/passwd',644,'root'],
        ['/etc/shadow',000,'root'],
        ['/etc/gshadow',000,'root'],
        ['/etc/cron.deny',600,'root'],
        ['/etc/anacrontab',600,'root'],
        ['/var',755,'root'],
        ['/var/spool',755,'root'],
        ['/var/spool/cron',700,'root'],
        ['/var/spool/cron/root',600,'root'],
        ['/var/spool/cron/crontabs/root',600,'root'],
        ['/www',755,'root'],
        ['/www/server',755,'root'],
        ['/root',550,'root'],
        ['/mnt',755,'root'],
        ['/home',755,'root'],
        ['/dev',755,'root'],
        ['/opt',755,'root'],
        ['/sys',555,'root'],
        ['/run',755,'root'],
        ['/tmp',777,'root']
    ]

    not_mode_list = []
    for d in dir_list:
        if not os.path.exists(d[0]): continue
        u_mode = public.get_mode_and_user(d[0])
        if u_mode['user'] != d[2]:
            not_mode_list.append("{} Current permissions: {} : {} Security permissions: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
        if int(u_mode['mode']) != d[1]:
            not_mode_list.append("{} Current permissions: {} : {} Security permissions: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
    
    if not_mode_list:
        return False,'The following system file or directory permissions are incorrect: <br />' + ("<br />".join(not_mode_list))

    return True,'Risk-free'

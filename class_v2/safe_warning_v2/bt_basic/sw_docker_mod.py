#!/usr/bin/python
# coding: utf-8

import sys, os, public
_title = 'Docker critical file permission checks'
_version = 1.0  # 版本
_ps = "Docker critical file permission checks"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-14'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_docker_mod.pl")
_tips = [
    "On the File page, set the correct permissions and owners for the specified directory or file",
    "docker.service and docker.socket require permission [644]",
    "docker directory chmod /etc/docker 755"
]
_help = ''
_remind = 'This solution strengthens the protection of Docker files and prevents intruders from tampering with Docker files. '


def check_run():
    dir_list = [
        ['/usr/lib/systemd/system/docker.service', 644, 'root'],
        ['/usr/lib/systemd/system/docker.socket', 644, 'root'],
        ['/etc/docker', 755, 'root']
        ]

    not_mode_list = []
    for d in dir_list:
        if not os.path.exists(d[0]):
            continue
        u_mode = public.get_mode_and_user(d[0])
        if u_mode['user'] != d[2]:
            not_mode_list.append("{} Current permissions: {} : {} Security permissions: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
        if int(u_mode['mode']) != d[1]:
            not_mode_list.append("{} Current permissions: {} : {} Security permissions: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
    if not_mode_list:
        return False, 'The following critical file or directory permission error:{}'.format('、'.join(not_mode_list))
    else:
        return True, "Risk-free"

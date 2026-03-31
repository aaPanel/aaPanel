#!/usr/bin/python
# coding: utf-8

import sys, os, public
_title = 'bootloader Configuring permissions'
_version = 1.0  # 版本
_ps = "bootloader Configuring permission checks"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_bootloader_mod.pl")
_tips = [
    "Configure secure permissions for grub according to the file suggested by the risk description",
    "If grub2, then: chmod 600 /boot/grub2/grub.cfg、chown root /boot/grub2/grub.cfg",
    "If grub, then: chmod 600 /boot/grub/grub.cfg、chown root /boot/grub/grub.cfg"
]
_help = ''
_remind = 'This scheme can strengthen the server grub interface protection, further prevent external intrusion server.'

def check_run():
    dir_list = [
        ['/boot/grub2/grub.cfg', 600, 'root'],
        ['/boot/grub/grub.cfg', 600, 'root']
        ]
    # 存放没有配置权限的文件
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
        return False, 'The following critical file or directory permissions are incorrect:{}'.format('、'.join(not_mode_list))
    else:
        return True, "Risk-free"

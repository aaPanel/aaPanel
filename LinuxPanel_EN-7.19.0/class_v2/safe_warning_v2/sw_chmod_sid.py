#!/usr/bin/python
# coding: utf-8

import os, public


_title = 'Check for files with suid and sgid permissions'
_version = 1.0  # 版本
_ps = "Check important files for suid and sgid permissions"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_chmod_sid.pl")
_tips = [
    "Use the chmod u-s/g-s [filename] command to change the permissions of the file",
]
_help = ''
_remind = 'This scheme removes the special permissions of important files, which can prevent intruders from using these files for privilege escalation.'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    exist_list = []
    # 列出重要文件，先判断是否存在
    file_list = ['/usr/bin/chage', '/usr/bin/gpasswd', '/usr/bin/wall', '/usr/bin/chfn', '/usr/bin/chsh', '/usr/bin/newgrp',
                 '/usr/bin/write', '/usr/sbin/usernetctl', '/bin/mount', '/bin/umount', '/bin/ping', '/sbin/netreport']
    for fl in file_list:
        if os.path.exists(fl):
           exist_list.append(fl)
    # find命令-perm 判断是否有suid或guid，有则返回该文件名
    result_str = public.ExecShell('find {} -type f -perm /04000 -o -perm /02000'.format(' '.join(exist_list)))[0].strip()
    result = '、'.join(result_str.split('\n'))
    if result:
        return False, 'The following files have sid privilege, chmod u-s or g-s remove sid bits: \"{}\"'.format(result)
    else:
        return True, 'Risk-free'

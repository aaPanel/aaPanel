#!/usr/bin/python
#coding: utf-8

import os,sys,re,public


_title = 'ssh access control list checking'
_version = 1.0  # 版本
_ps = "Set up an ssh login whitelist"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_hosts.pl")
_tips = [
    "add ALL:ALL in 【/etc/hosts.deny】",
    "add sshd:【visitor IP address】 in【/etc/hosts.allow】"
]
_help = ''
_remind = 'This scheme will block the rest of the IP except the white list to login the server, and enhance the security protection of the server. Note that this solution is risky; be sure to add an IP address to the server before you fix it.'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/hosts.deny'
    conf = public.ReadFile(cfile)
    if 'all:all' in conf or 'ALL:ALL' in conf:
        return True, 'Risk-free'
    else:
        return False, 'ssh login whitelist is not set'

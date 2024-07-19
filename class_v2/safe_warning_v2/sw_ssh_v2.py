#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = 'Whether to use encrypted remote administration ssh'
_version = 1.0  # 版本
_ps = "Detect whether secure socket layer encryption is used to transmit information to avoid eavesdropping on sensitive information"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_v2.pl")
_tips = [
    "Add or modify Protocol 2 in [/etc/ssh/sshd_config] file ",
    "Then run the command systemctl restart sshd to restart the process ",
]
_help = ''
_remind = 'This scheme can enhance the protection of SSH communication and avoid sensitive data leakage.'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/ssh/sshd_config'
    conf = public.readFile(cfile)
    rep = r"\nProtocol 2"
    tmp = re.search(rep, conf)
    if tmp:
        return True, 'Risk-free'
    else:
        return False, 'Remote administration of ssh without secure socket encryption'

#!/usr/bin/python
#coding: utf-8

import sys,re,os,public

_title = 'Use the graphical interface to check after restricting SSH login'
_version = 1.0                              # 版本
_ps = "Use the graphical interface to check after restricting SSH login"                      # 描述
_level = 0                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-14'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_forward.pl")
_tips = [
    "Modify X11Forwarding to no in [/etc/ssh/sshd_config]",
    ]
_help = ''
_remind = 'This can be used to enforce SSH login security and speed up SSH connections. Notethe fix turns off X11 graphical forwarding, so do not configure it if you need to use it. '

def check_run():
    conf = '/etc/ssh/sshd_config'
    if not os.path.exists(conf):
        return True, 'Risk-free'
    result = public.ReadFile(conf)
    rep = r'.*?X11Forwarding\s*?yes'
    tmp = re.search(rep, result)
    if tmp:
        if tmp.group()[0] == '#':
            return True, 'Risk-free'
        else:
            return False, 'SSH graphical forwarding is not disabled'
    return True, 'Risk-free'

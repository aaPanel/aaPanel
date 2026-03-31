#!/usr/bin/python
# coding: utf-8

import os, re, public


_title = 'Check if the command-line interface timeout is set'
_version = 1.0  # 版本
_ps = "Check if the command-line interface timeout is set"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_time_out.pl")
_tips = [
    "Add tmout=300 in the file [/etc/profile], and the waiting time is not more than 600 seconds ",
    "Execute source /etc/profile to make the configuration work ",
]
_help = ''
_remind = 'This solution will make the server command line over a certain period of time does not operate automatically shut down, can strengthen the security of the server. '


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/profile'
    conf = public.readFile(cfile)
    rep = r'(tmout|TMOUT)(\s*)=(\s*)([1-9][^0-9]|[1-9][0-9][^0-9]|[1-5][0-9][0-9][^0-9]|600[^0-9])'
    tmp = re.search(rep, conf)
    if tmp:
        return True, 'Risk-free'
    else:
        return False, 'No command line timeout is configured for exit'

#!/usr/bin/python
# coding: utf-8

import os, public

_title = 'Check for dangerous remote access files'
_version = 1.0  # 版本
_ps = "Check for dangerous remote access files:hosts.equiv、.rhosts、.netrc"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_risk_file.pl")
_tips = [
    "Delete the .rhosts and .netrc files in the home directory and delete the hosts.equiv file in the root directory",
    "Follow the prompts to find the risk file and delete it"
]
_help = ''
_remind = 'This solution removes all vulnerable files, preventing them from being exploited by hackers to gain access to the server. You can backup files before deleting them to prevent them from affecting the operation of your website. '

def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    result_list = []
    cfile = ['hosts.equiv', '.rhosts', '.netrc']
    for cf in cfile:
        file = public.ExecShell('find / -maxdepth 3 -name {}'.format(cf))
        if file[0]:
            result_list = result_list+file[0].split('\n')
    result = '、'.join(reform_list(result_list))
    if result:
        return False, 'High-risk files, delete the following files as soon as possible\"{}\"'.format(result)
    else:
        return True, 'Risk-free'


def reform_list(check_list):
    """处理列表里的空字符串"""
    return [i for i in check_list if (i is not None) and (str(i).strip() != '')]


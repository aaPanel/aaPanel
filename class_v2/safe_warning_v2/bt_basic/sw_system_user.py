#!/usr/bin/python
# coding: utf-8
# Date 2022/1/12

import sys,os

_title = 'System backdoor user detection'
_version = 1.0  # 版本
_ps = "System backdoor user detection"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2021-01-12'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_system_user.pl")
_tips = [
    "Delete backdoor user in command line",
    "Note: If there is a backdoor user, it means that your server has been invaded"
]
_help = ''
_remind = 'This scheme will remove the backdoor users with the same privileges as the root user, and enhance the protection of the server permission control. If it is a business requirement, this risk term is ignored. '
def check_run():
    '''
        @name 开始检测
        @author lkq<2021-01-12>
        @return tuple (status<bool>,msg<string>)
    '''
    ret=[]
    cfile = '/etc/passwd'
    if os.path.exists(cfile):
        f=open(cfile,'r')
        for i in f:
            i=i.strip().split(":")
            if i[2]=='0' and i[3]=='0':
                if i[0]=='root':continue
                ret.append(i[0])
    if ret:
        return False, 'There is a backdoor user: %s'%''.join(ret)
    return True, 'No backdoor users are currently found'
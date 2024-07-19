#!/usr/bin/python
# coding: utf-8

import os, sys, public

_title = 'Check nginx binaries for tampering'
_version = 1.0  # 版本
_ps = "Check nginx binaries for tampering"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_nginx_md5.pl")
_tips = [
    "Reinstall Nginx in panel [Software Store] - [Run Environment] ",
]
_help = ''
_remind = '/ WWW/server/nginx/sbin/nginx executable been tampered with, risk was invaded site. '


def check_run():
    '''
        @name 开始检测
        @author lwh<2023-11-21>
        @return tuple (status<bool>,msg<string>)
    '''
    nginx_path = '/www/server/nginx/sbin/nginx'
    nginx_md5 = '/www/server/panel/data/nginx_md5.pl'
    if not os.path.exists(nginx_path):
        return True, 'Risk-free'
    try:
        new_md5 = public.ExecShell('md5sum {}'.format(nginx_path))[0].strip().split(" ")[0]
        if os.path.exists(nginx_md5):
            old_md5 = public.ReadFile(nginx_md5).split(" ")[0]
            if new_md5 != old_md5:
                return False, "nginx file tampering has been detected（MD5：{}）".format(new_md5)
        return True, 'Risk-free'
    except:
        return True, 'Risk-free'

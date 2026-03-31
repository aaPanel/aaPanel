#!/usr/bin/python
# coding: utf-8

import os, sys, public

_title = 'Check if nginx binary files are tampered'
_version = 1.0  # 版本
_ps = "Check if nginx binary files are tampered"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_nginx_md5.pl")
_tips = [
    "Reinstall Nginx in the panel's [Software Store] - [Runtime Environment]",
    "Seek professional security team to conduct a comprehensive investigation of the server and remove backdoors"
]
_help = ''
_remind = 'Detected that the /www/server/nginx/sbin/nginx executable file has been tampered with, and the website is at risk of being compromised.'


def check_run():
    '''
        @name Start detection
        @author lwh<2023-11-21>
        @return tuple (status<bool>,msg<string>)
    '''
    nginx_path = '/www/server/nginx/sbin/nginx'
    nginx_md5 = '/www/server/panel/data/nginx_md5.pl'
    if not os.path.exists(nginx_path):
        return True, 'No risk'
    try:
        # new_md5 = public.ExecShell('md5sum {}'.format(nginx_path))[0].strip().split(" ")[0]
        new_md5 = public.FileMd5(nginx_path)
        if not new_md5:
            return True, 'No risk'
        if os.path.exists(nginx_md5):
            old_md5 = public.ReadFile(nginx_md5).strip().split(" ")[0]
            if new_md5 != old_md5:
                return False, "Detected nginx file tampering (MD5: {})".format(new_md5)
        return True, 'No risk'
    except:
        return True, 'No risk'

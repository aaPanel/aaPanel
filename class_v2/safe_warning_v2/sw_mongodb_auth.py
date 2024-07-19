#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = 'Whether to enable security authentication for MongoDB'
_version = 1.0  # 版本
_ps = "Check whether MongoDB security authentication is enabled"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_mongodb_auth.pl")
_tips = [
    "Turn on the security authentication switch in the aaPanel Databases MongoDB",
]
_help = ''
_remind = 'This is a great way to protect your database against hackers trying to steal data from your mongo database. '

def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    if not public.process_exists("mongod"):
        return True, 'Risk-free，The MongoDB service has not been started！'
    cfile = '{}/mongodb/config.conf'.format(public.get_setup_path())
    conf = public.readFile(cfile)
    rep = r".*authorization(\s*):(\s*)enabled"
    tmp = re.search(rep, conf)
    if tmp:
        return True, 'Risk-free'
    else:
        return False, 'MongoDB security authentication is not enabled'


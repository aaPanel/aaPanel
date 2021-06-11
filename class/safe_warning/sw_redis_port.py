#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Redis安全检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Redis security'
_version = 1.0                              # 版本
_ps = "Check whether the current Redis is safe"                 # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_redis_port.pl")
_tips = [
    "If not necessary, please do not configure Redis bind to 0.0.0.0",
    "If bind is 0.0.0.0, be sure to set an access password for Redis",
    "Do not use too simple password as Redis access password",
    "Once Redis has a security problem, this will cause the server to be invaded with a high probability, please be sure to deal with it carefully"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    p_file = '/www/server/redis/redis.conf'
    p_body = public.readFile(p_file)
    if not p_body: return True,'Rick-free'

    tmp = re.findall(r"^\s*bind\s+(0\.0\.0\.0)",p_body,re.M)
    if not tmp: return True,'Rick-free'

    tmp = re.findall(r"^\s*requirepass\s+(.+)",p_body,re.M)
    if not tmp: return False,'Reids allows public internet connection, but no Redis password is set, which is extremely dangerous, please deal with it immediately'

    redis_pass = tmp[0].strip()
    if not is_strong_password(redis_pass):
        return False, 'Redis access password is too simple, and there are security risks'

    return True,'无风险'


def is_strong_password(password):
    """判断密码复杂度是否安全

    非弱口令标准：长度大于等于7，分别包含数字、小写、大写、特殊字符。
    @password: 密码文本
    @return: True/False
    """

    if len(password) < 7:
        return False

    import re
    digit_reg = "[0-9]"  # 匹配数字 +1
    lower_case_letters_reg = "[a-z]"  # 匹配小写字母 +1
    upper_case_letters_reg = "[A-Z]"  # 匹配大写字母 +1
    special_characters_reg = r"((?=[\x21-\x7e]+)[^A-Za-z0-9])"  # 匹配特殊字符 +1

    regs = [digit_reg,
            lower_case_letters_reg,
            upper_case_letters_reg,
            special_characters_reg]

    grade = 0
    for reg in regs:
        if re.search(reg, password):
            grade += 1

    if grade == 4 or (grade >= 2 and len(password) >= 9):
        return True
    return False

#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh <lwh@bt.cn>
# -------------------------------------------------------------------
# Time: 2023-08-05
# -------------------------------------------------------------------
# PHP未关闭错误提示
# -------------------------------------------------------------------


import sys, os

os.chdir('/www/server/panel')
sys.path.append("class/")

import public, re, os

_title = 'PHP is giving an error message'
_version = 1.0  # 版本
_ps = "Check if PHP is turned off"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-8-5'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_php_display_errors.pl")
_tips = [
    "According to the risk description, find the corresponding version of PHP plugin in [Software Store] - [Running Environment], and in [Configuration Modification] page, set display_errors to off and save."
]

_help = ''
_remind = "PHP error prompts may reveal sensitive information about your site's applications; This solution prevents website information from leaking by turning off the [display_errors] option"
_type = 'web'


def check_run():
    path = "/www/server/php"
    # 获取目录下的文件夹
    dirs = os.listdir(path)
    result = []
    for dir in dirs:
        if dir in ["52", "53", "54", "55", "56", "70", "71", "72", "73", "74", "80", "81"]:
            file_path = path + "/" + dir + "/etc/php.ini"
            if os.path.exists(file_path):
                # 获取文件内容
                try:
                    php_ini = public.readFile(file_path)
                    if re.search("\ndisplay_errors\\s?=\\s?(.+)", php_ini):
                        status = re.findall("\ndisplay_errors\\s?=\\s?(.+)", php_ini)
                        if 'On' in status or 'on' in status:
                            result.append(dir[0]+'.'+dir[1])  # 中间加个.
                except:
                    pass
    if result:
        ret = "The PHP versions that do not turn off error messages are: {}".format('、'.join(result))
        return False, ret
    else:
        return True, "Risk-free"

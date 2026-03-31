#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh <lwh@bt.cn>
# -------------------------------------------------------------------
# Time: 2023-08-07
# -------------------------------------------------------------------
# PHP.ini挂马
# -------------------------------------------------------------------


import sys, os

os.chdir('/www/server/panel')
sys.path.append("class/")

import public, re, os

_title = 'PHP configuration file failure detection'
_version = 1.0  # 版本
_ps = "Check if PHP config file is suspended"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-8-7'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_php_backdoor.pl")
_tips = [
    "According to the risk description, find the corresponding version of PHP plugin in [Software Store] - [Running Environment]. ",
    "On the [Configuration] page, go to auto_prepend_file or auto_append_file, delete the rest, save and restart PHP."
]

_help = ''
_remind = 'This solution removes malicious code from php configuration files and suggests a full Trojan scan of the server to remove backdoor files and fix website vulnerabilities. '
_type = 'web'


def check_run():
    path = "/www/server/php"
    # 获取目录下的文件夹
    dirs = os.listdir(path)
    result = {}
    for dir in dirs:
        if dir in ["52", "53", "54", "55", "56", "70", "71", "72", "73", "74", "80", "81"]:
            file_path = path + "/" + dir + "/etc/php.ini"
            if os.path.exists(file_path):
                # 获取文件内容
                try:
                    php_ini = public.readFile(file_path)
                    if re.search("\nauto_prepend_file\\s?=\\s?(.+)", php_ini):
                        prepend = re.findall("\nauto_prepend_file\\s?=\\s?(.+)", php_ini)
                        if "data:;base64" in prepend[0]:
                            result[dir] = ["auto_prepend_file"]
                    if re.search("\nauto_append_file\\s?=\\s?(.+)", php_ini):
                        append = re.findall("\nauto_append_file\\s?=\\s?(.+)", php_ini)
                        if "data:;base64" in append[0]:
                            if dir in result:
                                result[dir].append("auto_append_file")
                            else:
                                result[dir] = ["auto_append_file"]
                except:
                    pass
    if result:
        ret = ""
        for i in result:
            ret += "【PHP" + i + "】A field where malicious code is present:" + ",".join(result[i]) + "\n"
        return False, ret
    else:
        return True, "Risk-free"

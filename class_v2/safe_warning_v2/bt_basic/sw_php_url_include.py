#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh
# -------------------------------------------------------------------
# Time: 2024-02-23
# -------------------------------------------------------------------
# PHP开启远程文件包含
# -------------------------------------------------------------------

import sys,os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Enable remote file inclusion in PHP'
_version = 1.0  # 版本
_ps = "PHP has the risk of remote file inclusion."  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2024-02-23'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_php_url_include.pl")
_tips = [
    'Set the "allow_url_include" configuration in the [php.ini] file to "Off"'
]

_help = ''
_remind = 'This solution can prevent the website from being exploited by hackers through remote inclusion vulnerabilities and control servers.'


def check_run():
    path = "/www/server/php"
    # 检查PHP目录是否存在
    if not os.path.exists(path):
        return True, 'Risk-free'  # PHP未安装

    # 获取目录下的文件夹
    dirs = os.listdir(path)
    resulit = []
    for dir in dirs:
        # 动态检查是否为有效的PHP版本目录（检查php.ini是否存在）
        file_path = os.path.join(path, dir, "etc", "php.ini")
        if os.path.exists(file_path):
            # 获取文件内容
            try:
                php_ini = public.readFile(file_path)
                if not php_ini:
                    continue
                # 查找include
                if re.search("\nallow_url_include\\s*=\\s*(\\w+)", php_ini):
                    include_php = re.search("\nallow_url_include\\s*=\\s*(\\w+)", php_ini).groups()[0]
                    if include_php.lower() == "off":
                        pass
                    else:
                        resulit.append(dir)
            except Exception as e:
                # 记录错误但继续检测其他版本
                public.print_log('Failed to detect the "php {} allow_url_include" setting:{}'.format(dir, e))
                continue
    if len(resulit) > 0:
        return False, 'The PHP versions that have remote inclusion vulnerabilities are as follows：【" + ",".join(resulit) + "】. Please set "allow_url_include" to "Off" in the php.ini file.'
    else:
        return True, "Risk-free"

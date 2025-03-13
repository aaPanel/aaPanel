#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# PHP存在版本泄露
# -------------------------------------------------------------------

# import sys,os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import re,public,os


_title = 'PHP version leaked'
_version = 1.0                              # 版本
_ps = "PHP version leaked"          # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_php_expose.pl")
_tips = [
    "Set [expose_php] in the [php.ini] file and configure it to Off",
    "Tips: Set [expose_php] in the [php.ini] file and configure it to Off"
    ]

_help = ''
_remind = 'This solution can prevent the disclosure of sensitive information on the website and reduce the possibility of server intrusion. '


def check_run():
    path ="/www/server/php"
    #获取目录下的文件夹
    dirs = os.listdir(path)
    resulit=[]
    for dir in dirs:
        if dir in ["52","53","54","55","56","70","71","72","73","74","80","81"]:
            file_path=path+"/"+dir+"/etc/php.ini"
            if os.path.exists(file_path):
                #获取文件内容
                try:
                    php_ini = public.readFile(file_path)
                    #查找expose_php
                    if re.search("\nexpose_php\\s*=\\s*(\\w+)",php_ini):
                        expose_php = re.search("\nexpose_php\\s*=\\s*(\\w+)",php_ini).groups()[0]
                        if expose_php.lower() == "off":
                            pass
                        else:
                            resulit.append(dir)
                except:
                    pass
    if resulit:
        return False, "The affected php versions are as follows: ["+",".join(resulit)+"], please set expose_php to Off in php.ini"
    else:
        return True, "Risk-free"

# check_run()
#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# Nginx 版本泄露
# -------------------------------------------------------------------

import re, public, os
_title = 'Nginx version leaked'
_version = 1.0  # 版本
_ps = "Nginx version leaked"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_nginx_server.pl")
_tips = [
    "Set [server_tokens off;] in the [/www/server/nginx/conf/nginx.conf] file;",
    "Tips：server_tokens off;"
]
_help = ''
_remind = 'This solution enhances server protection and reduces the risk of your website being compromised. '
def check_run():
    '''
        @name 检测nginx版本泄露
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/nginx/conf/nginx.conf'):
        try:
            info_data = public.ReadFile('/www/server/nginx/conf/nginx.conf')
            if info_data:
                if re.search('server_tokens off;', info_data):
                    return True, 'Risk-free'
                else:
                    return False, 'The current version of Nginx is leaked, please add or modify the parameter server_tokens to off; in the Nginx configuration file, for example: server_tokens off;'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'

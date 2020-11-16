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
# 网站证书检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Website certificate (SSL)'
_version = 1.0                              # 版本
_ps = "Check whether all websites deploy SSL"             # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_site_ssl.pl")
_tips = [
    "Please consider deploying an SSL certificate for your website to improve its security"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    site_list = public.M('sites').field('id,name').select()

    not_ssl_list = []
    for site_info in site_list:
        ng_conf_file = '/www/server/panel/vhost/nginx/' + site_info['name'] + '.conf'
        if not os.path.exists(ng_conf_file): continue
        s_body = public.readFile(ng_conf_file)
        if not s_body: continue
        if s_body.find('ssl_certificate') == -1:
            not_ssl_list.append(site_info['name'])
        
    if not_ssl_list:
        return False ,'The following sites do not deploy SSL certificates: <br />' + ('<br />'.join(not_ssl_list))
    
    return True,'Rick-free'
        
        
    

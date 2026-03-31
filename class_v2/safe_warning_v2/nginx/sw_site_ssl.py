#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 网站证书检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Website certificate (SSL)'
_version = 2.0
_ps = "Check if production environment websites have security certificates deployed"
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_site_ssl.pl")
_tips = [
    "Please consider deploying SSL certificates for your production environment websites to enhance website security"
    ]
_help = ''
_remind = 'SSL certificates ensure the security of website communication and prevent data from being stolen by hackers during transmission.'


def is_test_domain(domain):
    """
    Determine if it is a test/development domain
    Test domain characteristics:
    1. Contains keywords like test, dev, staging, demo
    2. Uses IP address as domain name
    3. Uses example domains like example.com, test.com
    4. Uses random string domains (e.g., hhhhh.com, wegweg.com)
    """
    domain_lower = domain.lower().strip()

    # 检查是否为IP地址
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain_lower):
        return True

    # 测试/开发域名关键字
    test_keywords = [
        'test', 'testing', 'tests',
        'dev', 'devel', 'development',
        'staging', 'stage',
        'demo', 'demos',
        'example', 'examples',
        'localhost', 'local',
        'temp', 'temporary',
        'lab', 'labs',
        'beta',
        'alpha'
    ]

    # 检查是否包含测试关键字
    for keyword in test_keywords:
        if keyword in domain_lower:
            return True

    # 检查是否为常见的示例域名
    example_domains = [
        'example.com', 'example.org', 'example.net',
        'test.com', 'tests.com',
        'demo.com', 'demos.com'
    ]
    if domain_lower in example_domains:
        return True

    # 检查是否为随机字符串域名（连续重复字符或无意义字符串）
    # 例如：hhhhh.com, wegweg.com, abcabc.com
    if re.match(r'^([a-z])\1{3,}', domain_lower):  # 连续重复字符
        return True
    if re.match(r'^([a-z]{3,})\1+$', domain_lower):  # 重复字符串
        return True

    # 检查域名长度，短于5个字符的可能是测试域名
    if len(domain_lower.split('.')[0]) < 4:
        return True

    return False


def check_run():
    '''
        @name Start detection
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    site_list = public.M('sites').field('id,name').select()

    not_ssl_list = []
    test_domain_list = []

    for site_info in site_list:
        domain = site_info['name']

        # Skip test domains
        if is_test_domain(domain):
            test_domain_list.append(domain)
            continue

        ng_conf_file = '/www/server/panel/vhost/nginx/' + domain + '.conf'
        if not os.path.exists(ng_conf_file): continue
        s_body = public.readFile(ng_conf_file)
        if not s_body: continue
        if s_body.find('ssl_certificate') == -1:
            not_ssl_list.append(domain)

    # If there are production environment sites without SSL deployed
    if not_ssl_list:
        msg = 'The following production environment sites do not have SSL certificates deployed:\n' + '\n'.join(not_ssl_list)
        if test_domain_list:
            msg += '\n\nSkipped test/development domains:\n' + '\n'.join(test_domain_list[:5])
            if len(test_domain_list) > 5:
                msg += f' and {len(test_domain_list)} other test domains'
        return False, msg

    # All production environment sites have SSL deployed
    return True, 'No risk'

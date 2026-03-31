#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wpl <2026-03-04>
# +-------------------------------------------------------------------

# RingH23攻击套件检测
# +-------------------------------------------------------------------

import os
import sys
import re
import glob

_title = 'Detecting if the server is infected with the RingH23 attack suite'
_version = 1.0
_ps = 'Detect the RingH23 attack characteristics such as the /var/adm/ directory, ld.so.preload, and udev rules.'
_ignore = os.path.exists('/www/server/panel/data/warning/ignore/sw_ringh23_attack.pl')
_tips = [
    'Use export RING04H={uuid} to disable Rootkit hiding features',
    'Delete the malicious module path /var/adm/ from /etc/ld.so.preload',
    'Delete all files under the /var/adm/{uuid} directory',
    'Delete the /etc/udev/rules.d/99-{uuid}.rules rule file'
]

# 帮助信息
_help = ''

# 修复提醒
_remind = 'RingH23 attack suite may result in malicious code being implanted into the website'


def check_run():
    '''
        @name RingH23攻击套件检测
        @return tuple (status<bool>,msg<string>)
    '''
    risk_items = []

    # ==== 检测点1: 检查 /var/adm/ 目录 ====
    if os.path.exists('/var/adm/'):
        try:
            for item in os.listdir('/var/adm/'):
                # 匹配UUID格式: 32位16进制 或 带横线的标准UUID
                if re.match(r'^[a-f0-9]{32}$', item) or \
                   re.match(r'^[a-f0-9-]{36}$', item):
                    risk_items.append('/var/adm/{}'.format(item))
        except:
            pass

    # ==== 检测点2: 检查 ld.so.preload ====
    preload_file = '/etc/ld.so.preload'
    if os.path.exists(preload_file):
        try:
            with open(preload_file, 'r') as f:
                content = f.read().strip()
                if content and ('libutilkeybd.so' in content or '/var/adm/' in content):
                    risk_items.append('Abnormal preload module: {}'.format(content))
        except:
            pass

    # ==== 检测点3: 检查 udev 规则 ====
    udev_path = '/etc/udev/rules.d'
    if os.path.exists(udev_path):
        try:
            for f in glob.glob('{}/99-*.rules'.format(udev_path)):
                risk_items.append('Abnormal udev rule: {}'.format(f))
        except:
            pass

    # ==== 返回结果 ====
    if risk_items:
        msg = 'RingH23 attack signatures detected:<br/>' + '<br/>'.join(risk_items)
        return False, msg

    return True, 'No RingH23 attack signatures detected'

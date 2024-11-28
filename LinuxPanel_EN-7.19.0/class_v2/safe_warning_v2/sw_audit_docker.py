#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = 'Whether to enable Docker log audit check'
_version = 1.0  # 版本
_ps = "Whether to enable Docker log audit check"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-13'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_audit_docker.pl")
_tips = [
    "Add -w /usr/bin/docker -k docker from [/etc/audit/rules.d/audit.rules] file",
    "Restart auditd process: systemctl restart auditd"
]
_help = ''


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    audit_path = '/etc/audit/audit.rules'
    if not os.path.exists(audit_path):
        return False, 'Risky, the auditd audit tool is not installed'
    # auditctl -l命令列出当前auditd规则，匹配是否有对docker做审计记录
    result = public.ExecShell('auditctl -l')[0].strip()
    rep = '/usr/bin/docker'
    if re.search(rep, result):
        return True, 'Risk-free'
    else:
        return False, 'Risky, the docker audit log is not enabled'


#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = 'Audit logs are kept forever'
_version = 1.0  # 版本
_ps = "Check whether the audit log is automatically deleted when it is full"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_audit_log_keep.pl")
_tips = [
    "In [/etc/audit/auditd.conf] max_log_file_action changes ROTATE to KEEP_LOGS",
    "Restart auditd service: systemctl restart auditd"
]
_help = ''


def check_run():
    cfile = '/etc/audit/auditd.conf'
    if not os.path.exists(cfile):
        return False, 'Risky，The auditd audit tool is not installed'
    result = public.ReadFile(cfile)
    # 默认是rotate，日志满了后循环日志，keep_logs会保留旧日志
    rep = r'max_log_file_action\s*=\s(.*)'
    tmp = re.search(rep, result)
    if tmp:
        if 'keep_logs'.lower() == tmp.group(1).lower():
            return True, 'Risk-free'
    return False, 'The current max_log_file_action value is {}, it should be KEEP_LOGS'.format(tmp.group(1))

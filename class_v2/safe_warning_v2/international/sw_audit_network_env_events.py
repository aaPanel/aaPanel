import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of events that modify system network environment'
_version = 1.0
_ps = 'Check if collection of events that modify system network environment is enabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_network_env_events.pl")
_tips = [
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`:",
    "-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale",
    "-w /etc/issue -p wa -k system-locale",
    "-w /etc/issue.net -p wa -k system-locale",
    "-w /etc/hosts -p wa -k system-locale",
    "-w /etc/sysconfig/network -p wa -k system-locale",
    "-w /etc/sysconfig/network-scripts/ -p wa -k system-locale",
    "Restart: `service auditd restart`"
]
_help = ''
_remind = 'Record changes to network environment files or system calls. The following parameters monitor sethostname (set system hostname) or setdomainname (set system domain name) system calls and write audit events on system call exit. Other parameters monitor /etc/issue and /etc/issue.net files (messages displayed before login), /etc/hosts (file containing hostname and associated IP addresses), /etc/sysconfig/network file and /etc/sysconfig/network-scripts/ directory (containing network interface scripts and configuration).'


def check_run():
    try:
        # 只检测centos系统
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, 'Audit rule file not detected'
        body = '\n'.join(contents)
        rules = [
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+sethostname\s+-S\s+setdomainname\s+-k\s+system-locale\s*$', '-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale'),
            (r'^\s*-w\s+/etc/issue\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/issue -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/issue\.net\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/issue.net -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/hosts\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/hosts -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/sysconfig/network\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/sysconfig/network -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/sysconfig/network-scripts/\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/sysconfig/network-scripts/ -p wa -k system-locale')
        ]
        missing = []
        for p, line in rules:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, 'Missing audit rules: ' + ';'.join(missing)
        return True, 'No risk'
    except:
        return True, 'No risk'
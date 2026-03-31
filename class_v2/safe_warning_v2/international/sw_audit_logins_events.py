import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of login and logout events'
_version = 2.0
_ps = 'Check if audit login and failed attempt events are enabled (only detected when auditd is installed)'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_logins_events.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Add the following to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`",
    "-w /var/log/lastlog -p wa -k logins",
    "-w /var/run/faillock/ -p wa -k logins",
    "Reload and restart audit: service auditd restart"
]
_help = ''
_remind = 'Without auditing login and failed attempts, brute force attacks and abnormal logins are difficult to track; after enabling logins rules, lastlog/faillock changes will be recorded, improving auditing and traceability capabilities'


def is_auditd_installed():
    """Check if auditd is installed"""
    if os.path.exists('/usr/sbin/auditd') or os.path.exists('/sbin/auditd'):
        return True
    try:
        if os.path.exists('/usr/bin/rpm'):
            result = os.popen('rpm -q audit 2>/dev/null').read()
            if result and 'audit' in result.lower() and 'not installed' not in result.lower():
                return True
        elif os.path.exists('/usr/bin/dpkg'):
            result = os.popen('dpkg -l auditd 2>/dev/null').read()
            if result and 'auditd' in result.lower() and 'no packages found' not in result.lower():
                return True
    except:
        pass
    return False


def check_run():
    try:
        # 首先检查auditd是否安装
        if not is_auditd_installed():
            return True, 'auditd is not installed, skipping detection'

        # auditd已安装，检查审计规则
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, 'Audit rule file not detected: /etc/audit/rules.d/audit.rules or /etc/audit/audit.rules is missing'
        body = '\n'.join(contents)
        reqs = [
            (r'^\s*-w\s+/var/log/lastlog\s+-p\s+wa\s+-k\s+logins\s*$', '-w /var/log/lastlog -p wa -k logins')
        ]
        # 仅当faillock目录存在时才检测其规则（与修复方案保持一致）
        if os.path.exists('/var/run/faillock/'):
            reqs.append(
                (r'^\s*-w\s+/var/run/faillock/\s+-p\s+wa\s+-k\s+logins\s*$', '-w /var/run/faillock/ -p wa -k logins')
            )
        missing = []
        for p, line in reqs:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, 'Missing logins audit rules: ' + ';'.join(missing)
        return True, 'No risk'
    except:
        return True, 'No risk'

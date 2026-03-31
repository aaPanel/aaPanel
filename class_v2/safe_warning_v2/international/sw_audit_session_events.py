import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of session initiation information'
_version = 2.0
_ps = 'Check if collection of session initiation information is enabled (only detected when auditd is installed)'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_session_events.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`:",
    "-w /var/run/utmp -p wa -k session",
    "-w /var/log/wtmp -p wa -k logins",
    "-w /var/log/btmp -p wa -k logins",
    "Restart: `service auditd restart`"
]
_help = ''
_remind = 'Monitoring these files for changes may alert system administrators to logins occurring at unusual times, which may indicate intruder activity'


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
            return False, 'Audit rule file not detected'
        body = '\n'.join(contents)
        rules = [
            (r'^\s*-w\s+/var/run/utmp\s+-p\s+wa\s+-k\s+session\s*$', '-w /var/run/utmp -p wa -k session'),
            (r'^\s*-w\s+/var/log/wtmp\s+-p\s+wa\s+-k\s+(session|logins)\s*$', '-w /var/log/wtmp -p wa -k logins'),
            (r'^\s*-w\s+/var/log/btmp\s+-p\s+wa\s+-k\s+(session|logins)\s*$', '-w /var/log/btmp -p wa -k logins')
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

import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of events that modify user/group information'
_version = 2.0
_ps = 'Check if account and password file change events are monitored (only detected when auditd is installed)'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_identity_events.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Add the following to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`",
    "-w /etc/group -p wa -k identity",
    "-w /etc/passwd -p wa -k identity",
    "-w /etc/gshadow -p wa -k identity",
    "-w /etc/shadow -p wa -k identity",
    "-w /etc/security/opasswd -p wa -k identity",
    "Reload and restart audit: service auditd restart"
]
_help = ''
_remind = 'If account and password file write/attribute changes are not audited, account tampering will be difficult to trace; after enabling identity rules, abnormal changes will be recorded and retrieved, improving intrusion detection and tracking capabilities'


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
            (r'^\s*-w\s+/etc/group\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/group -p wa -k identity'),
            (r'^\s*-w\s+/etc/passwd\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/passwd -p wa -k identity'),
            (r'^\s*-w\s+/etc/gshadow\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/gshadow -p wa -k identity'),
            (r'^\s*-w\s+/etc/shadow\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/shadow -p wa -k identity'),
            (r'^\s*-w\s+/etc/security/opasswd\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/security/opasswd -p wa -k identity')
        ]
        miss_lines = []
        for p, line in reqs:
            if not re.search(p, body, re.M):
                miss_lines.append(line)
        if miss_lines:
            return False, 'Missing identity audit rules: ' + ';'.join(miss_lines)
        return True, 'No risk'
    except:
        return False, 'Abnormal detection of account and password file changes'

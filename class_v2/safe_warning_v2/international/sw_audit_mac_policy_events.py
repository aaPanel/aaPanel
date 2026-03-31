import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of events that modify system mandatory access controls'
_version = 2.0
_ps = 'Check if events that modify system mandatory access controls are collected (only detected when auditd is installed)'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_mac_policy_events.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`: -w /etc/selinux/ -p wa -k MAC-policy",
    "In systems using apparmor, also add:",
    "-w /etc/apparmor/ -p wa -k MAC-policy",
    "-w /etc/apparmor.d/ -p wa -k MAC-policy",
    "Reload and restart audit: service auditd restart"
]
_help = ''
_remind = 'Without auditing mandatory access control policy changes, policy tampering and security context abnormalities are difficult to track; after enabling MAC-policy rules, SELinux/AppArmor policy write and attribute changes will be recorded, improving auditing and traceability capabilities'


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
        need_sel = os.path.isdir('/etc/selinux')
        need_app = os.path.isdir('/etc/apparmor') or os.path.isdir('/etc/apparmor.d')
        missing_lines = []
        if need_sel and not re.search(r'^\s*-w\s+/etc/selinux/\s+-p\s+wa\s+-k\s+MAC-policy\s*$', body, re.M):
            missing_lines.append('SELinux: -w /etc/selinux/ -p wa -k MAC-policy')
        if need_app:
            ok1 = re.search(r'^\s*-w\s+/etc/apparmor/\s+-p\s+wa\s+-k\s+MAC-policy\s*$', body, re.M)
            ok2 = re.search(r'^\s*-w\s+/etc/apparmor\.d/\s+-p\s+wa\s+-k\s+MAC-policy\s*$', body, re.M)
            if not ok1:
                missing_lines.append('AppArmor: -w /etc/apparmor/ -p wa -k MAC-policy')
            if not ok2:
                missing_lines.append('AppArmor: -w /etc/apparmor.d/ -p wa -k MAC-policy')
        if missing_lines:
            return False, 'Missing MAC-policy audit rules: ' + ';'.join(missing_lines)
        return True, 'No risk'
    except:
        return True, 'No risk'

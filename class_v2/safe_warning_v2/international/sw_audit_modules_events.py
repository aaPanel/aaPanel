import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of kernel module loading and unloading'
_version = 2.0
_ps = 'Check if collection of kernel module loading and unloading is enabled (only detected when auditd is installed)'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_modules_events.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`:",
    "-w /sbin/insmod -p x -k modules",
    "-w /sbin/rmmod -p x -k modules",
    "-w /sbin/modprobe -p x -k modules",
    "-a always,exit -F arch=b64 -S init_module -S delete_module -k modules",
    "Reload and restart audit: service auditd restart"
]
_help = ''
_remind = 'Without auditing kernel module loading/unloading, kernel-level backdoors and stability abnormalities are difficult to track; after enabling modules rules, insmod/rmmod/modprobe and init_module/delete_module system calls will be recorded, improving auditing and traceability capabilities'


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
        missing_lines = []
        if not re.search(r'^\s*-w\s+/sbin/insmod\s+-p\s+x\s+-k\s+modules\s*$', body, re.M):
            missing_lines.append('-w /sbin/insmod -p x -k modules')
        if not re.search(r'^\s*-w\s+/sbin/rmmod\s+-p\s+x\s+-k\s+modules\s*$', body, re.M):
            missing_lines.append('-w /sbin/rmmod -p x -k modules')
        if not re.search(r'^\s*-w\s+/sbin/modprobe\s+-p\s+x\s+-k\s+modules\s*$', body, re.M):
            missing_lines.append('-w /sbin/modprobe -p x -k modules')
        if not re.search(
                r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+init_module\s+.*-S\s+delete_module\s+.*-k\s+modules\s*$',
                body, re.M):
            missing_lines.append('-a always,exit -F arch=b64 -S init_module -S delete_module -k modules')
        if missing_lines:
            return False, 'Missing modules audit rules: ' + ';'.join(missing_lines)
        return True, 'No risk'
    except:
        return True, 'No risk'

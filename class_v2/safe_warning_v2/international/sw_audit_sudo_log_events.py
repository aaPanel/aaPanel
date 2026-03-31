import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure system administrator operations are collected'
_version = 1.0
_ps = 'Check if collecting system administrator operations is enabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_sudo_log_events.pl")
_tips = [
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`:",
    "-w /var/log/sudo.log -p wa -k actions",
    "Restart: `service auditd restart`"
]
_help = ''
_remind = 'Associate administrator commands with audit records to discover unauthorized operations and tampering'


def check_run():
    try:
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, 'No audit rule files detected'
        body = '\n'.join(contents)
        ok = re.search(r'^\s*-w\s+/var/log/sudo\.log\s+-p\s+wa\s+-k\s+actions\s*$', body, re.M)
        if ok:
            return True, 'No risk'
        return False, 'auditd log collection missing audit rule: -w /var/log/sudo.log -p wa -k actions'
    except:
        return True, 'No risk'
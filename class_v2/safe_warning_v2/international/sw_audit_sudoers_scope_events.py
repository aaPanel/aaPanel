import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure changes to system administration scope (sudoers) are collected'
_version = 1.0
_ps = 'Check if monitoring sudoers file and directory changes is enabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_sudoers_scope_events.pl")
_tips = [
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`:",
    "-w /etc/sudoers -p wa -k scope",
    "-w /etc/sudoers.d/ -p wa -k scope",
    "Restart: `service auditd restart`"
]
_help = ''
_remind = 'Monitor changes to system administration scope. If the system is properly configured to force system administrators to first log in as themselves and then use sudo commands to execute privileged commands, scope changes can be monitored. The /etc/sudoers file is written when files or their attributes change. Audit records will be tagged with the identifier "scope". Changes in the /etc/sudoers file may indicate unauthorized changes to the scope of system administrator activities.'


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
        rules = [
            (r'^\s*-w\s+/etc/sudoers\s+-p\s+wa\s+-k\s+scope\s*$', '-w /etc/sudoers -p wa -k scope'),
            (r'^\s*-w\s+/etc/sudoers\.d/\s+-p\s+wa\s+-k\s+scope\s*$', '-w /etc/sudoers.d/ -p wa -k scope')
        ]
        missing = []
        for p, line in rules:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, 'Missing audit rules: ' + '；'.join(missing)
        return True, 'No risk'
    except:
        return True, 'No risk'
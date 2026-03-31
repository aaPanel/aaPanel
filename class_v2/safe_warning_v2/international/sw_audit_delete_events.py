import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of user file deletion events'
_version = 1.0
_ps = 'Check if user file deletion event collection is enabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_delete_events.pl")
_tips = [
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`: -a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`: -a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete",
    "Reload and restart audit: service auditd restart"
]
_help = ''
_remind = 'Without auditing delete/rename events, it will be difficult to track when protected files are deleted or tampered by non-privileged users; after enabling delete rules, key file deletion/rename behaviors will be recorded, improving traceability and compliance capabilities'


def check_run():
    try:
        # 仅限centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, 'Audit rule file not detected: /etc/audit/rules.d/audit.rules or /etc/audit/audit.rules is missing'
        body = '\n'.join(contents)
        reqs = [
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+unlink\s+.*-S\s+unlinkat\s+.*-S\s+rename\s+.*-S\s+renameat\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+delete\s*$', '-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+unlink\s+.*-S\s+unlinkat\s+.*-S\s+rename\s+.*-S\s+renameat\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+delete\s*$', '-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete')
        ]
        missing = []
        for p, line in reqs:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, 'Missing delete audit rules: ' + ';'.join(missing)
        return True, 'No risk'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of unsuccessful unauthorized file access attempts'
_version = 1.0
_ps = 'Check if unauthorized file access failure log collection is enabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_access_failed_events.pl")
_tips = [
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`: -a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`: -a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`: -a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`: -a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access",
    "Reload and restart audit: service auditd restart"
]
_help = ''
_remind = 'Without auditing access failure events, privilege escalation attempts and probing behaviors are difficult to track; after enabling access rules, file access failures due to EACCES/EPERM for non-privileged users will be recorded, improving auditing and traceability capabilities'

def check_run():
    try:
        # 仅centos系统检测
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
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EACCES\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b64 ... -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EACCES\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b32 ... -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EPERM\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b64 ... -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EPERM\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b32 ... -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access')
        ]
        missing = []
        for p, desc in reqs:
            if not re.search(p, body, re.M):
                missing.append(desc)
        if missing:
            return False, 'Missing access audit rules: ' + ';'.join(missing)
        return True, 'No risk'
    except:
        return True, 'No risk'
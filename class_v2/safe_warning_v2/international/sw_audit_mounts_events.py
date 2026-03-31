import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure collection of successful filesystem mounts'
_version = 1.0
_ps = 'Check if monitoring of non-privileged users executing mount system calls is enabled to identify abnormal mount behavior'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_mounts_events.pl")
_tips = [
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`:",
    "-a always,exit -F arch=b64 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts",
    "-a always,exit -F arch=b32 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts",
    "Restart: `service auditd restart`"
]
_help = ''
_remind = 'Monitor the use of mount system calls. mount (and umount) system calls control the mounting and unmounting of filesystems. The following parameters configure the system to create audit records when non-privileged users use the mount system call. It is very unusual for non-privileged users to mount filesystems to the system. Tracking mount commands provides evidence to system administrators that external media may have been mounted (based on checking the mount source and confirming it is an external media type), but it does not definitively indicate that data has been exported to the media. Administrators who wish to determine if data has been exported must also track successful open, create, and truncate system calls that require write access to files under mount points on external media filesystems. This can give a fair indication of where writes occurred. The only way to truly prove it is to track successful writes to external media. Tracking write system calls may quickly fill audit logs, which is not recommended.'


def check_run():
    try:
        # 只检查centos系统
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
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+mount\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+mounts\s*$', '-a always,exit -F arch=b64 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+mount\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+mounts\s*$', '-a always,exit -F arch=b32 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts')
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
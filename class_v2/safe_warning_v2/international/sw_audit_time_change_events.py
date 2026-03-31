import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure events that modify date and time information are collected'
_version = 2.0
_ps = 'Check if monitoring time-related system calls is enabled'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_time_change_events.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Add to `/etc/audit/rules.d/audit.rules` and `/etc/audit/audit.rules`:",
    "-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change",
    "-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change",
    "-a always,exit -F arch=b64 -S clock_settime -k time-change",
    "-a always,exit -F arch=b32 -S clock_settime -k time-change",
    "-w /etc/localtime -p wa -k time-change",
    "Restart: `service auditd restart`"
]
_help = ''
_remind = 'Capture events that modify system date and/or time. Set parameters in this section to determine if adjtimex (adjusting kernel clock), settimeofday (setting time, using time and timezone structures) for stime (seconds since January 1, 1970) or clock_settime (allowing setting multiple internal clocks and timers) system calls have been executed, and always write audit records to /var/log/audit.log file when exiting, using the identifier "time-change" to tag records. Unexpected changes to system date and/or time may be a sign of malicious activity on the system.'


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
        if not is_auditd_installed():
            return False, 'auditd is not installed, cannot check audit rules'

        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, 'No audit rule files detected'
        body = '\n'.join(contents)
        rules = [
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+adjtimex\s+-S\s+settimeofday\s+-k\s+time-change\s*$', '-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+adjtimex\s+-S\s+settimeofday\s+-S\s+stime\s+-k\s+time-change\s*$', '-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+clock_settime\s+-k\s+time-change\s*$', '-a always,exit -F arch=b64 -S clock_settime -k time-change'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+clock_settime\s+-k\s+time-change\s*$', '-a always,exit -F arch=b32 -S clock_settime -k time-change'),
            (r'^\s*-w\s+/etc/localtime\s+-p\s+wa\s+-k\s+time-change\s*$', '-w /etc/localtime -p wa -k time-change')
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

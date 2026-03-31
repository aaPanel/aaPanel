import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure RDS is disabled'
_version = 1.0
_ps = 'Check if RDS kernel module is disabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_rds_disabled.pl")
_tips = [
    'Create or edit `/etc/modprobe.d/CIS.conf` and add: install rds /bin/true'
]
_help = ''
_remind = 'Reliable Datagram Sockets (RDS) protocol is a transport layer protocol that provides low-latency, high-bandwidth communication between cluster nodes.\nIf the protocol is not used, it is recommended not to load the kernel module and disable the service to reduce the potential attack surface.'


def check_run():
    try:
        d = '/etc/modprobe.d'
        if not os.path.isdir(d):
            return True, 'No risk'
        ok = False
        for name in os.listdir(d):
            if not name.endswith('.conf'):
                continue
            fp = os.path.join(d, name)
            body = public.readFile(fp) or ''
            if re.search(r'^\s*(?!#)\s*install\s+rds\s+/bin/true\s*$', body, re.M):
                ok = True
                break
        if ok:
            return True, 'No risk'
        return False, 'Disable rule not configured in /etc/modprobe.d/*.conf: install rds /bin/true'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure TIPC is disabled'
_version = 1.0
_ps = 'Check if TIPC kernel module is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_tipc_disabled.pl")
_tips = [
    'Create or edit /etc/modprobe.d/CIS.conf and add: install tipc /bin/true'
]
_help = ''
_remind = 'Disable unnecessary protocols to reduce potential attack surface'


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
            if re.search(r'^\s*(?!#)\s*install\s+tipc\s+/bin/true\s*$', body, re.M):
                ok = True
                break
        if ok:
            return True, 'No risk'
        return False, 'Disable rule not configured in /etc/modprobe.d/*.conf: install tipc /bin/true'
    except:
        return True, 'No risk'
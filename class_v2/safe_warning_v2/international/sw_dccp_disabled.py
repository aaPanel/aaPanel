import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure DCCP is disabled'
_version = 1.0
_ps = 'Check if DCCP kernel module is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_dccp_disabled.pl")
_tips = [
    'Create or edit `/etc/modprobe.d/CIS.conf` and add: `install dccp /bin/true`',
    'Optional: `echo blacklist dccp >> /etc/modprobe.d/CIS.conf`',
    'Unload loaded module: `modprobe -r dccp`'
]
_help = ''
_remind = 'Datagram Congestion Control Protocol (DCCP) is a transport layer protocol supporting streaming media and telephony. If the protocol is not required, it is recommended not to install the driver to reduce the potential attack surface.'


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
            if re.search(r'^\s*(?!#)\s*install\s+dccp\s+/bin/true\s*$', body, re.M):
                ok = True
                break
        if ok:
            return True, 'No risk'
        return False, 'Disable rule not configured in /etc/modprobe.d/*.conf: install dccp /bin/true'
    except:
        return True, 'No risk'
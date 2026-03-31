import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure SCTP is disabled'
_version = 1.0
_ps = 'Check if SCTP protocol module is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_sctp_disabled.pl")
_tips = [
    'Create or edit `/etc/modprobe.d/CIS.conf` and add: install sctp /bin/true'
]
_help = ''
_remind = 'Stream Control Transmission Protocol (SCTP) is a transport layer protocol used to support message-oriented communications, with several message streams in one connection.\nIf the protocol is not used, it is recommended not to load the kernel module and disable the service to reduce the potential attack surface.'


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
            if re.search(r'^\s*(?!#)\s*install\s+sctp\s+/bin/true\s*$', body, re.M):
                ok = True
                break
        if ok:
            return True, 'No risk'
        return False, 'Disable rule not configured in /etc/modprobe.d/*.conf: install sctp /bin/true'
    except:
        return True, 'No risk'
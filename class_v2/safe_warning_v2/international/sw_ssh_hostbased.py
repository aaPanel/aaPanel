import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure SSH HostbasedAuthentication is disabled'
_version = 1.0
_ps = 'Whether to disable SSH HostbasedAuthentication'
_level = 2
_date = '2025-11-18'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_hostbased.pl")
_tips = [
    "Edit `/etc/ssh/sshd_config` and set `HostbasedAuthentication` to: no",
    "Then restart SSH service",
]
_help = ''
_remind = 'The hostbasedauthentication parameter specifies whether to allow authentication via trusted hosts of .rhosts or /etc/hosts.equiv users, and successful public key client host authentication.\nThis option only applies to ssh protocol version 2.'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        values = re.findall(r'^\s*(?!#)\s*HostbasedAuthentication\s+(\S+)', conf, re.M)
        if not values:
            return True, 'No risk'
        val = values[-1].strip().lower()
        if val in ('yes', 'on', 'true'):
            return False, 'HostbasedAuthentication is not disabled'
        return True, 'No risk'
    except:
        return True, 'No risk'
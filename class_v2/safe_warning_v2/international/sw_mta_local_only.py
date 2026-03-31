import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure mail transfer agent is in local-only mode'
_version = 1.0
_ps = 'Check if mail transfer agent configuration is restricted to local only'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_mta_local_only.pl")
_tips = [
    "Set: postconf -e 'inet_interfaces = 127.0.0.1'",
    "Restart: systemctl restart postfix"
]
_help = ''
_remind = 'If the system is a mail server, please ignore this check item. It is recommended to configure MTA to handle local mail only. Configuring non-mail server MTA to local only can significantly reduce exposure and exploitation risk.'


def check_run():
    try:
        cfile = '/etc/postfix/main.cf'
        if not os.path.exists(cfile):
            return True, 'No risk'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        vals = re.findall(r'^\s*(?!#)\s*inet_interfaces\s*=\s*(\S+)', conf, re.M)
        if not vals:
            return False, 'inet_interfaces=127.0.0.1 not configured in /etc/postfix/main.cf'
        v = vals[-1].split('#')[0].strip().lower()
        if v != '127.0.0.1':
            return False, 'inet_interfaces not set to 127.0.0.1 (/etc/postfix/main.cf)'
        return True, 'No risk'
    except:
        return True, 'No risk'
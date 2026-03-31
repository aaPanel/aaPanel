import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure telnet service is not enabled'
_version = 1.0
_ps = 'Check if telnet service is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_inetd_telnet_disabled.pl")
_tips = [
    "Comment or delete lines starting with `telnet` in `/etc/inetd.conf` and `/etc/inetd.d/*`",
    "Set `disable = yes` for `telnet` service in `/etc/xinetd.conf` and `/etc/xinetd.d/*`"
]
_help = ''
_remind = 'The telnet-server package contains the telnet daemon, which accepts connections from users on other systems via the telnet protocol. The telnet protocol is insecure and unencrypted.\nUsing an unencrypted transmission medium can allow users with access to sniff network traffic to steal credentials. The ssh package provides encrypted sessions and stronger security.'


def _inetd_has_service(names):
    cfgs = ['/etc/inetd.conf']
    found = []
    for c in cfgs:
        if not os.path.exists(c):
            continue
        body = public.readFile(c) or ''
        for line in body.splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            for n in names:
                if s.startswith(n + ' '):
                    found.append(c + ':' + s)
    ddir = '/etc/inetd.d'
    if os.path.isdir(ddir):
        for name in os.listdir(ddir):
            fp = os.path.join(ddir, name)
            body = public.readFile(fp) or ''
            for line in body.splitlines():
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                for n in names:
                    if s.startswith(n + ' '):
                        found.append(fp + ':' + s)
    return found


def _xinetd_service_enabled(names):
    files = ['/etc/xinetd.conf']
    ddir = '/etc/xinetd.d'
    if os.path.isdir(ddir):
        for name in os.listdir(ddir):
            files.append(os.path.join(ddir, name))
    enabled = []
    for fp in files:
        if not os.path.exists(fp):
            continue
        body = public.readFile(fp) or ''
        for n in names:
            if re.search(r'^\s*service\s+' + re.escape(n) + r'\b', body, re.M):
                dism = re.search(r'^\s*disable\s*=\s*(\w+)\s*$', body, re.M)
                if dism and dism.group(1).lower() == 'yes':
                    continue
                enabled.append(fp)
    return enabled


def check_run():
    try:
        names = ['telnet']
        inetd = _inetd_has_service(names)
        xinetd = _xinetd_service_enabled(names)
        if inetd or xinetd:
            return False, 'telnet service is enabled: {}'.format(','.join(inetd + xinetd))
        return True, 'No risk'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure rsh server is not enabled'
_version = 1.0
_ps = 'Check if rsh/rlogin/rexec is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_inetd_rsh_disabled.pl")
_tips = [
    "Comment or delete lines starting with `shell`, `login`, `exec` in `/etc/inetd.conf` and `/etc/inetd.d/*`",
    "Set `disable = yes` for `rsh`/`rlogin`/`rexec` services in `/etc/xinetd.conf` and `/etc/xinetd.d/*`",
    "Example: Edit `/etc/xinetd.d/rsh`, `/etc/xinetd.d/rlogin`, `/etc/xinetd.d/rexec` and set `disable = yes`"
]
_help = ''
_remind = 'Berkeley rsh-server (rsh, rlogin, rexec) packages contain legacy services that exchange credentials in clear text.\nThese legacy services contain significant security risks and have been replaced by the more secure SSH package.'


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
            # rsh相关服务可能以service rsh/rlogin/rexec出现，也可能通过disable字段控制
            if re.search(r'^\s*service\s+' + re.escape(n) + r'\b', body, re.M):
                dism = re.search(r'^\s*disable\s*=\s*(\w+)\s*$', body, re.M)
                if dism and dism.group(1).lower() == 'yes':
                    continue
                enabled.append(fp)
    return enabled


def check_run():
    try:
        inetd_names = ['shell', 'login', 'exec']
        xinetd_names = ['rsh', 'rlogin', 'rexec']
        inetd = _inetd_has_service(inetd_names)
        xinetd = _xinetd_service_enabled(xinetd_names)
        if inetd or xinetd:
            return False, 'rsh related services are enabled: {}'.format(','.join(inetd + xinetd))
        return True, 'No risk'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure tftp service is not enabled'
_version = 1.0
_ps = 'Check if tftp service is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_inetd_tftp_disabled.pl")
_tips = [
    "Comment or delete lines starting with `tftp` in `/etc/inetd.conf` and `/etc/inetd.d/*`",
    "Set `disable = yes` for `tftp` service in `/etc/xinetd.conf` and `/etc/xinetd.d/*`"
]
_help = ''
_remind = 'TFTP does not support authentication and does not ensure confidentiality or integrity of data. It is recommended to disable TFTP unless there is a special need.\nIn this case, extra care must be taken when configuring the service.'


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
        names = ['tftp']
        inetd = _inetd_has_service(names)
        xinetd = _xinetd_service_enabled(names)
        if inetd or xinetd:
            return False, 'tftp service is enabled: {}'.format(','.join(inetd + xinetd))
        return True, 'No risk'
    except:
        return True, 'No risk'
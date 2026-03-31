import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure jffs2 file system mount is disabled'
_version = 1.0
_ps = 'Check if jffs2 file system module is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_jffs2_disabled.pl")
_tips = [
    'Create or edit `/etc/modprobe.d/CIS.conf` and add: install jffs2 /bin/true'
]
_help = ''
_remind = 'jffs2 (Journaled Flash File System v2) is a log-structured file system used on flash devices. Removing support for unneeded file system types reduces the local attack surface of the system. If this file system type is not needed, it should be disabled.'


def check_run():
    try:
        d = '/etc/modprobe.d'
        if not os.path.isdir(d):
            return True, 'No risk'
        for name in os.listdir(d):
            if not name.endswith('.conf'):
                continue
            fp = os.path.join(d, name)
            body = public.readFile(fp) or ''
            if re.search(r'^\s*(?!#)\s*install\s+jffs2\s+/bin/true\s*$', body, re.M):
                return True, 'No risk'
        return False, 'Disable rule not configured in /etc/modprobe.d/*.conf: install jffs2 /bin/true'
    except:
        return True, 'No risk'
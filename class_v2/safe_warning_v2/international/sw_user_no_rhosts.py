import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure no users have .rhosts files'
_version = 1.0
_ps = 'Check for .rhosts file existence'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_no_rhosts.pl")
_tips = [
    "Find and delete: `find /home -type f -name .rhosts -exec rm -f {} +`",
    "Delete root home: `rm -f /root/.rhosts`"
]
_help = ''
_remind = 'Although .rhosts files are not sent by default, users can easily create them. This operation only makes sense when .rhosts support is allowed in the /etc/pam.conf file.\nEven if .rhosts file support is disabled in /etc/pam.conf, they may have been introduced from other systems and may contain information useful to attackers on other systems.'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, 'No risk'
        hits = []
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            name, home = parts[0], parts[5]
            if not home or home == '/':
                continue
            try:
                rhosts_path = os.path.join(home, '.rhosts')
                if os.path.isfile(rhosts_path):
                    hits.append('{}:{}'.format(name, rhosts_path))
            except:
                pass
        if hits:
            return False, '.rhosts detected: {} (total: {})'.format('、'.join(hits), len(hits))
        return True, 'No risk'
    except:
        return True, 'No risk'
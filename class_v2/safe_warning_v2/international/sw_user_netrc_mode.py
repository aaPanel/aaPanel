import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = "Ensure user '.netrc' files are not globally or group accessible"
_version = 1.0
_ps = "Check if .netrc permissions are not globally or group accessible"
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_netrc_mode.pl")
_tips = [
    "Find and fix: find /home -type f -name .netrc -exec chmod 600 {} +",
    "Fix root: chmod 600 /root/.netrc"
]
_help = ''
_remind = 'While system administrators can establish secure permissions for users .netrc files, users can easily override these permissions.\n.netrc files may contain unencrypted passwords that could be used to attack other systems'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, 'No risk'
        bad = []
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
                path = os.path.join(home, '.netrc')
                if os.path.isfile(path):
                    mode = os.stat(path).st_mode & 0o777
                    if mode != 0o600:
                        bad.append('{}:{}:{}'.format(name, path, format(mode, 'o')))
            except:
                pass
        if bad:
            return False, '.netrc files with insecure permissions exist: {}'.format('、'.join(bad))
        return True, 'No risk'
    except:
        return True, 'No risk'
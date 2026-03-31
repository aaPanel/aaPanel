import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure no users have .netrc files'
_version = 1.0
_ps = 'Check for .netrc file existence'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_no_netrc.pl")
_tips = [
    "Batch delete: find /home -type f -name .netrc -exec rm -f {} +",
    "Delete root: rm -f /root/.netrc"
]
_help = ''
_remind = '.netrc files contain data for logging into remote hosts via FTP for file transfers. .netrc files pose a serious security risk as they store passwords in unencrypted form.\nEven if FTP is disabled, user accounts may have brought .netrc files from other systems, which may pose a risk to those systems.'


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
                path = os.path.join(home, '.netrc')
                if os.path.isfile(path):
                    hits.append('{}:{}'.format(name, path))
            except:
                pass
        if hits:
            return False, '.netrc files exist: {}'.format('、'.join(hits))
        return True, 'No risk'
    except:
        return True, 'No risk'
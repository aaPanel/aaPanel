import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure no users have .forward files'
_version = 1.0
_ps = 'Check for .forward file existence'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_no_forward.pl")
_tips = [
    "Batch delete: find /home -type f -name .forward -exec rm -f {} +",
    "Delete root: rm -f /root/.forward"
]
_help = ''
_remind = 'Prevent sensitive emails from being forwarded or executing unexpected commands that cause data leakage and risks. The .forward file specifies email addresses used to forward user mail. Using .forward files poses security risks as sensitive data may be inadvertently transferred outside the organization.'


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
                path = os.path.join(home, '.forward')
                if os.path.isfile(path):
                    hits.append('{}:{}'.format(name, path))
            except:
                pass
        if hits:
            return False, '.forward files exist: {}'.format('、'.join(hits))
        return True, 'No risk'
    except:
        return True, 'No risk'
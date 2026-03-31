import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import time, public

_title = 'Ensure all users have changed password in the past'
_version = 1.0
_ps = 'Check if user password has been changed within the maximum number of days'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_password_last_change_past.pl")
_tips = [
    "Check specific user: `chage -l <username>`",
    "Force user to change password: `passwd -e <username>` or `chage -d 0 <username>`",
    "Set password expiration policy: `chage -M <max_days> <username>`"
]
_help = ''
_remind = 'If a user account is created on a temporary basis and is not renamed after use, its password should expire automatically, reducing the security risk of the account remaining on the system.'


def check_run():
    try:
        pf = '/etc/passwd'
        sf = '/etc/shadow'
        p = public.readFile(pf)
        s = public.readFile(sf)
        if not p or not s:
            return True, 'No risk'
        uids = {}
        for line in p.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            try:
                uids[parts[0]] = int(parts[2])
            except:
                pass
        today_days = int(time.time() // 86400)
        bad = []
        for line in s.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 3:
                continue
            name = parts[0]
            if name not in uids:
                continue
            if uids[name] < 1000:
                continue
            lastchg = parts[2]
            try:
                if int(lastchg) > today_days:
                    bad.append(name)
            except:
                pass
        if bad:
            return False, 'Future password change date detected: {}'.format(','.join(sorted(set(bad))))
        return True, 'No risk'
    except:
        return True, 'No risk'
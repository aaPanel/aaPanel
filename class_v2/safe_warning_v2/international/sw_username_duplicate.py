import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure duplicate usernames do not exist'
_version = 1.0
_ps = 'Check for duplicate usernames'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_username_duplicate.pl")
_tips = [
    "Detect duplicate usernames: `awk -F: '{print $1}' /etc/passwd | sort | uniq -d`",
    "Fix example: `usermod -l <new_username> <old_username>`"
]
_help = ''
_remind = 'Although .rhosts files are not sent by default, users can easily create them. This operation only makes sense when .rhosts support is allowed in the /etc/pam.conf file.\nEven if .rhosts file support is disabled in /etc/pam.conf, they may have been introduced from other systems and may contain information useful to attackers on other systems.'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, 'No risk'
        names = {}
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            name = parts[0]
            names[name] = names.get(name, 0) + 1
        dup = [n for n, c in names.items() if c > 1]
        if dup:
            return False, 'Duplicate usernames exist: {}'.format(','.join(dup))
        return True, 'No risk'
    except:
        return True, 'No risk'
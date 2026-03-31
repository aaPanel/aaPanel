import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure no duplicate group names exist'
_version = 1.0
_ps = 'Check if user groups have duplicate group names'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_groupname_duplicate.pl")
_tips = [
    "Detect duplicate group names: `awk -F: '{print $1}' /etc/group | sort | uniq -d`",
    "List duplicate group names: `awk -F: 'NR==FNR{a[$1]++;next} a[$1]>1{print $1}' /etc/group /etc/group`",
    "Fix: `groupmod -n <new-group-name> <old-group-name>`",
    "Second method: Click [System Reinforcement] - [Equal Protection Reinforcement] - [Access Control], check user audit, and adjust user group name according to risk description"
]
_help = ''
_remind = 'Duplicate group names can cause confusion in group permission management; after fixing, it ensures clear permission boundaries and responsibility attribution'


def check_run():
    try:
        gf = '/etc/group'
        body = public.readFile(gf)
        if not body:
            return True, 'No risk'
        names = []
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 1:
                continue
            names.append(parts[0])
        dup = [n for n in names if names.count(n) > 1]
        if dup:
            return False, 'Duplicate group names exist: {}'.format(','.join(set(dup)))
        return True, 'No risk'
    except:
        return True, 'No risk'
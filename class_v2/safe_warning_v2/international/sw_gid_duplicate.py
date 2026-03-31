import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure duplicate GIDs do not exist'
_version = 1.0
_ps = 'Check if user groups have duplicate GIDs'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_gid_duplicate.pl")
_tips = [
    "Detect duplicate GIDs: `awk -F: '{print $3}' /etc/group | sort | uniq -d`",
    "List groups sharing GID: `awk -F: 'NR==FNR{a[$3]++;next} a[$3]>1{print $1\":\"$3}' /etc/group /etc/group`",
    "Fix example: `groupmod -g <new-gid> <group-name>`, and migrate files: `find / -group <old-gid> -exec chgrp <group-name> {} +`",
    "Second method: Click [System Reinforcement] - [Equal Protection Reinforcement] - [Access Control], check user audit, and adjust user group ID according to risk description"
]
_help = ''
_remind = 'Duplicate GIDs can cause access control and audit confusion; after fixing, it ensures clear permission boundaries and responsibility attribution'


def check_run():
    try:
        gf = '/etc/group'
        body = public.readFile(gf)
        if not body:
            return True, 'No risk'
        gid_map = {}
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 3:
                continue
            name, gid = parts[0], parts[2]
            try:
                k = int(gid)
            except:
                continue
            gid_map.setdefault(k, []).append(name)
        dup = ['{}:{}'.format(k, ','.join(v)) for k, v in gid_map.items() if len(v) > 1]
        if dup:
            return False, 'Duplicate GIDs exist: {}'.format(';'.join(dup))
        return True, 'No risk'
    except:
        return True, 'No risk'
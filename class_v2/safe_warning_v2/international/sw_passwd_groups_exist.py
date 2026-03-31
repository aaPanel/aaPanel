import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure all groups in /etc/passwd exist in /etc/group'
_version = 1.0
_ps = 'Check if there are undefined GIDs in passwd file'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_passwd_groups_exist.pl")
_tips = [
    "Detect missing GIDs: `comm -23 <(awk -F: '{print $4}' /etc/passwd | sort -n | uniq) <(awk -F: '{print $3}' /etc/group | sort -n | uniq)`",
    "Create placeholder for missing groups: `groupadd -g <GID> grp_<GID>` (adjust group name as needed)"
]
_help = ''
_remind = 'Over time, system administration errors and changes may result in groups being defined in /etc/passwd but not in /etc/group. Groups defined in the /etc/passwd file but not in the /etc/group file pose a threat to system security because group permissions are not properly managed.'


def check_run():
    try:
        pf = '/etc/passwd'
        gf = '/etc/group'
        p_body = public.readFile(pf)
        g_body = public.readFile(gf)
        if not p_body or not g_body:
            return True, 'No risk'
        gids_p = set()
        for line in p_body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) >= 4:
                try:
                    gids_p.add(int(parts[3]))
                except:
                    pass
        gids_g = set()
        for line in g_body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) >= 3:
                try:
                    gids_g.add(int(parts[2]))
                except:
                    pass
        missing = [str(g) for g in sorted(gids_p - gids_g)]
        if missing:
            return False, 'GIDs without group definition: {} (source: /etc/passwd field 4)'.format(','.join(missing))
        return True, 'No risk'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure duplicate UIDs do not exist'
_version = 1.0
_ps = 'Check for duplicate UIDs'
_level = 3
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_uid_duplicate.pl")
_tips = [
    "Click [System Hardening] plugin, go to Compliance Hardening-Access Control-User Audit, check users with duplicate UIDs. If the duplicate UID user is not needed, you can delete it",
]
_help = ''
_remind = 'Although the useradd program does not allow you to create duplicate user IDs (UIDs), administrators can manually edit the /etc/passwd file and change the UID field.\nUsers must be assigned unique UIDs to ensure accountability and ensure proper access protection.'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, 'No risk'
        uid_map = {}
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            name, uid = parts[0], parts[2]
            try:
                k = int(uid)
            except:
                continue
            uid_map.setdefault(k, []).append(name)
        dup = ['{}:{}'.format(k, ','.join(v)) for k, v in uid_map.items() if len(v) > 1]
        if dup:
            return False, 'Duplicate UIDs exist: {}'.format('；'.join(dup))
        return True, 'No risk'
    except:
        return True, 'No risk'
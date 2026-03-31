import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure /tmp partition has nosuid option set'
_version = 1.0
_ps = 'Check if nosuid prohibits creating setuid files in /tmp'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_tmp_nosuid.pl")
_tips = [
    'First method for Debian/Ubuntu: Edit `/etc/fstab` and add nosuid option, add the following',
    '`tmpfs /tmp tmpfs defaults,nodev,nosuid,noexec 0 0`',
    'Execute the following command to remount /tmp: mount -o remount,nosuid /tmp',
    'Second method for CentOS systems:',
    'Edit /etc/systemd/system/local-fs.target.wants/tmp.mount file and add nosuid option:',
    'Options=mode=1777,strictatime,noexec,nodev,nosuid',
    'Execute the following command to remount /tmp: mount -o remount,nosuid /tmp'
]
_help = ''
_remind = 'Since the /tmp filesystem is only used for temporary file storage, set this option to ensure users cannot create setuid files in /tmp.'


def check_run():
    try:
        mounts = public.ReadFile('/proc/mounts')
        if mounts:
            for line in mounts.splitlines():
                parts = line.split()
                if len(parts) < 4:
                    continue
                if parts[1] == '/tmp':
                    opts = parts[3].split(',')
                    if 'nosuid' in opts:
                        return True, 'No risk'
                    return False, 'nosuid mount option not set for /tmp'
        unit = '/etc/systemd/system/local-fs.target.wants/tmp.mount'
        if os.path.exists(unit):
            body = public.ReadFile(unit) or ''
            if 'Options=' in body and 'nosuid' in body:
                return True, 'No risk'
        return False, 'nosuid mount option not set for /tmp'
    except:
        return True, 'No risk'
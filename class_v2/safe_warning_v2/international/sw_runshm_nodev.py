import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure /run/shm partition has nodev option set'
_version = 1.0
_ps = 'Check if nodev is set to prevent creation of special devices'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_runshm_nodev.pl")
_tips = [
    'Example mount line: tmpfs /run/shm tmpfs defaults,nodev,nosuid,noexec 0 0',
    'Edit /etc/fstab to add nodev to /run/shm mount entry, and run: mount -o remount,nodev /run/shm'
]
_help = ''
_remind = 'Prevent device file creation on shared memory partition'


def check_run():
    try:
        # Only detect Ubuntu systems
        if not isUbuntu():
            return True, 'No risk'
        mounts = public.ReadFile('/proc/mounts')
        if not mounts:
            return True, 'No risk'
        for line in mounts.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            if parts[1] == '/run/shm':
                opts = parts[3].split(',')
                if 'nodev' in opts:
                    return True, 'No risk'
                return False, 'nodev mount option not set for /run/shm'
        return True, 'No risk'
    except:
        return True, 'No risk'

def isUbuntu(self):
    try:
        if os.path.exists('/etc/lsb-release'):
            body = public.readFile('/etc/lsb-release') or ''
            if 'DISTRIB_ID=Ubuntu' in body:
                return True
        return False
    except:
        return False
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure SELinux or AppArmor is installed'
_version = 1.0
_ps = 'Check if SELinux or AppArmor is installed'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_mac_system_installed.pl")
_tips = [
    "Install SELinux (CentOS/RHEL): yum install selinux-policy-targeted policycoreutils",
    "Install SELinux (Debian/Ubuntu): apt-get install selinux",
    "Install AppArmor (Debian/Ubuntu): apt-get install apparmor apparmor-utils"
]
_help = ''
_remind = 'SELinux and AppArmor provide mandatory access control. Without a mandatory access control system installed, only the default discretionary access control system can be used.'


def check_run():
    try:
        selinux_paths = [
            '/etc/selinux',
            '/usr/sbin/selinuxenabled',
            '/usr/sbin/sestatus',
            '/usr/bin/getenforce'
        ]
        apparmor_paths = [
            '/etc/apparmor',
            '/etc/apparmor.d',
            '/sbin/apparmor_status',
            '/usr/sbin/aa-status'
        ]
        has_sel = any(os.path.exists(p) for p in selinux_paths)
        has_app = any(os.path.exists(p) for p in apparmor_paths)
        if has_sel or has_app:
            return True, 'No risk'
        missing = []
        for p in selinux_paths + apparmor_paths:
            if not os.path.exists(p):
                missing.append(p)
        return False, 'Mandatory access control not installed (missing component paths: {})'.format(','.join(missing[:6]))
    except:
        return True, 'No risk'
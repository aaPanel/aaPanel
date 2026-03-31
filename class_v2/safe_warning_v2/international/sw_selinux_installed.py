import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure SELinux is installed'
_version = 1.0
_ps = 'Check if SELinux components are installed'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_selinux_installed.pl")
_tips = [
    "Install SELinux base components: yum install libselinux"
]
_help = ''
_remind = 'Installing SELinux provides stronger access control and isolation capabilities for the system'


def check_run():
    try:
        # Only detect CentOS systems
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        paths = [
            '/usr/sbin/selinuxenabled',
            '/usr/sbin/sestatus',
            '/usr/bin/getenforce',
            '/usr/lib64/libselinux.so',
            '/usr/lib/libselinux.so'
        ]
        for p in paths:
            if os.path.exists(p):
                return True, 'No risk'
        return False, 'SELinux commands or libraries not detected (selinuxenabled/sestatus/getenforce or libselinux.so)'
    except:
        return True, 'No risk'
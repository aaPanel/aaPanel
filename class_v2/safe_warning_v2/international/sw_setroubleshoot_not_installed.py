import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure SETroubleshoot is not installed'
_version = 1.0
_ps = 'Check if SETroubleshoot is installed'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_setroubleshoot_not_installed.pl")
_tips = [
    "Uninstall: yum remove setroubleshoot",
    "Disable and stop service: systemctl disable --now setroubleshoot"
]
_help = ''
_remind = 'The SETroubleshoot service notifies desktop users of SELinux denials through a user-friendly interface. This service provides important information about configuration errors, unauthorized intrusions, and other potential errors.\nThe SETroubleshoot service is an unnecessary daemon running on the server, especially when X Windows is disabled.'


def check_run():
    try:
        # Only detect CentOS systems
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        paths = [
            '/usr/sbin/setroubleshootd',
            '/usr/bin/sealert',
            '/usr/libexec/setroubleshootd',
            '/usr/lib/systemd/system/setroubleshoot.service'
        ]
        for p in paths:
            if os.path.exists(p):
                return False, 'SETroubleshoot component detected: {}'.format(p)
        return True, 'No risk'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure MCS Translation is not installed'
_version = 1.0
_ps = 'Check if mcstrans component is uninstalled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_mcstrans_not_installed.pl")
_tips = [
    "Uninstall: `yum remove mcstrans`"
]
_help = ''
_remind = 'The mcstransd daemon provides category label information to client processes requesting information. Label translation is defined in /etc/selinux/targeted/setrans.conf. Since this service is not frequently used, remove it to reduce the amount of potentially vulnerable code running on the system.'


def check_run():
    try:
        paths = [
            '/usr/sbin/mcstransd',
            '/usr/lib/systemd/system/mcstrans.service'
        ]
        for p in paths:
            if os.path.exists(p):
                return False, 'mcstrans component detected: {}'.format(p)
        return True, 'No risk'
    except:
        return True, 'No risk'
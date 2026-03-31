import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure the talk client is not installed'
_version = 1.0
_ps = 'Check if the talk client is uninstalled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_talk_client_not_installed.pl")
_tips = [
    "Uninstall (CentOS/RHEL): yum remove talk",
    "Uninstall (Debian/Ubuntu): apt-get remove talk"
]
_help = ''
_remind = 'This software poses security risks when communicating using unencrypted protocols, as unencrypted communication is easily intercepted. It is recommended to remove the talk client.'


def check_run():
    try:
        names = ['talk']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, 'Talk client detected: {}'.format(','.join(found))
        return True, 'No risk'
    except:
        return True, 'No risk'
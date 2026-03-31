import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure the telnet client is not installed'
_version = 1.0
_ps = 'Check if the telnet client is uninstalled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_telnet_client_not_installed.pl")
_tips = [
    "Uninstall (CentOS/RHEL): yum remove telnet",
    "Uninstall (Debian/Ubuntu): apt-get remove telnet"
]
_help = ''
_remind = 'The telnet protocol is insecure and unencrypted. Using an unencrypted transport medium may allow unauthorized users to steal credentials.\nThe ssh package provides encrypted sessions and stronger security, and is included in most Linux distributions.'


def check_run():
    try:
        names = ['telnet']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, 'Telnet client detected: {}'.format(','.join(found))
        return True, 'No risk'
    except:
        return True, 'No risk'
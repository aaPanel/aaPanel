import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure NIS client is not installed'
_version = 1.0
_ps = 'Check if NIS client is uninstalled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_nis_client_not_installed.pl")
_tips = [
    "Uninstall (CentOS/RHEL): yum remove ypbind",
    "Uninstall (Debian/Ubuntu): apt-get remove nis"
]
_help = ''
_remind = 'NIS is essentially an insecure system, vulnerable to DoS attacks, buffer overflows, and poor authentication for querying NIS maps. NIS has largely been replaced by protocols such as LDAP. It is recommended to remove this service.'


def check_run():
    try:
        names = ['ypbind']
        dirs = ['/usr/sbin', '/sbin', '/usr/bin', '/bin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, 'NIS client components detected: {}'.format(','.join(found))
        return True, 'No risk'
    except:
        return True, 'No risk'
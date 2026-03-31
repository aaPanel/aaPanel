import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure LDAP client is not installed'
_version = 1.0
_ps = 'Check if LDAP client is uninstalled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ldap_client_not_installed.pl")
_tips = [
    "Uninstall (CentOS/RHEL): yum remove openldap-clients",
    "Uninstall (Debian/Ubuntu): apt-get remove ldap-utils"
]
_help = ''
_remind = 'If the system does not need to act as an LDAP client, it is recommended to remove the software to reduce the potential attack surface.'


def check_run():
    try:
        names = ['ldapsearch', 'ldapmodify', 'ldapadd']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, 'LDAP client tools detected: {}'.format(','.join(found))
        return True, 'No risk'
    except:
        return True, 'No risk'
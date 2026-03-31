import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure rsh client is not installed'
_version = 1.0
_ps = 'Check if rsh/rcp/rlogin client is uninstalled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_rsh_client_not_installed.pl")
_tips = [
    "Uninstall (Debian/Ubuntu): apt-get remove rsh-client rsh-redone-client",
    "Check for legacy symlinks: ls -l /usr/bin/rsh /usr/bin/rcp /usr/bin/rlogin",
    "If symlinks exist, it is recommended to delete: rm /usr/bin/rsh /usr/bin/rcp /usr/bin/rlogin"
]
_help = ''
_remind = 'These legacy clients contain significant security risks and have been replaced by the more secure ssh package. Even if the server is removed, it is best to ensure that clients are also removed to prevent users from inadvertently trying to use these commands and exposing their credentials.\nNote: Removing the rsh package will remove the rsh, rcp, and rlogin clients.'


def check_run():
    try:
        names = ['rsh', 'rcp', 'rlogin']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, 'rsh series client tools detected: {}'.format(','.join(found))
        return True, 'No risk'
    except:
        return True, 'No risk'
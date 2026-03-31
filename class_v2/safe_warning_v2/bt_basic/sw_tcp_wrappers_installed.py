import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure TCP Wrappers is installed'
_version = 1.0
_ps = 'Check if TCP Wrappers is installed'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_tcp_wrappers_installed.pl")
_tips = [
    "CentOS system: execute installation command: yum install tcp_wrappers",
    "Ubuntu/Debian system: execute apt-get install tcpd"
]
_help = ''
_remind = 'TCP Wrappers provides a simple access list and standardized logging method for services that support it.<br>It is recommended to use TCP Wrappers for all services that support it.'


def check_run():
    try:
        paths = [
            '/usr/sbin/tcpd',
            '/lib64/libwrap.so',
            '/lib/libwrap.so',
            '/usr/lib/libwrap.so',
            '/usr/lib64/libwrap.so'
        ]
        for p in paths:
            try:
                if os.path.exists(p):
                    return True, 'No risk'
            except:
                pass
        return False, 'TCP Wrappers is not installed'
    except:
        return True, 'No risk'
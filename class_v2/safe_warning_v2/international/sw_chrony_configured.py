import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure chrony is configured'
_version = 1.0
_ps = 'Check if chrony is configured'
_level = 2
_date = '2025-11-22'
_ignore = os.path.exists("data/warning/ignore/sw_chrony_configured.pl")
_tips = [
    'Add or edit server line in `/etc/chrony.conf`: server <remote-server>',
    'Set in `/etc/sysconfig/chronyd`: OPTIONS="-u chrony", or in `/usr/lib/systemd/system/chronyd.service` ExecStart contains `-u chrony`',
    'Enable and restart: systemctl enable --now chronyd'
]
_help = ''
_remind = 'chrony is a daemon implementing the Network Time Protocol (NTP) for synchronizing system clocks across various systems using highly accurate sources. Synchronization can be configured as client and/or server. If chrony is used on the system, having the correct configuration is essential for ensuring time synchronization works properly.\nThis recommendation applies only if chrony is used on the system.'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        conf_file = '/etc/chrony.conf'
        miss = []
        if os.path.exists(conf_file):
            conf = public.readFile(conf_file) or ''
            has_server = re.findall(r'^\s*(?!#)\s*(server|pool)\s+\S+', conf, re.M)
            if not has_server:
                miss.append('Missing server/pool line (/etc/chrony.conf)')
        syscfg = '/etc/sysconfig/chronyd'
        unitf = '/usr/lib/systemd/system/chronyd.service'
        checked_u = False
        if os.path.exists(syscfg):
            s = public.readFile(syscfg) or ''
            checked_u = True
            if '-u chrony' not in s:
                miss.append('chronyd is not running as chrony user (missing -u chrony)')
        elif os.path.exists(unitf):
            s = public.readFile(unitf) or ''
            checked_u = True
            if '-u chrony' not in s:
                miss.append('chronyd is not running as chrony user (missing -u chrony)')
        if miss:
            return False, 'chrony configuration is not standard: {}'.format(','.join(miss))
        return True, 'No risk'
    except:
        return True, 'No risk'
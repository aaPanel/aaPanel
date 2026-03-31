import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure NTP is configured'
_version = 1.1
_ps = 'Check if NTP configuration is standardized'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ntp_configured.pl")
_tips = [
    'Edit `/etc/ntp.conf`: add the following',
    '`restrict -4 default kod nomodify notrap nopeer noquery`',
    '`restrict -6 default kod nomodify notrap nopeer noquery` (required only for IPv6 environments)',
    'Enable and restart: `systemctl enable --now ntpd`'
]
_help = ''
_remind = 'Proper NTP configuration ensures normal time synchronization and improves log consistency'


def check_ipv6_enabled():
    '''Check if IPv6 is enabled on the system'''
    try:
        # Method 1: Check if network interface has IPv6 address
        output, err = public.ExecShell('ip -6 addr show 2>/dev/null | grep -c "inet6"')
        if output.strip() and int(output.strip()) > 0:
            return True
    except:
        pass

    try:
        # Method 2: Check kernel parameter
        value = public.readFile('/proc/sys/net/ipv6/conf/all/disable_ipv6')
        if value and value.strip() != '1':
            return True
    except:
        pass

    try:
        # Method 3: Try ping6 localhost
        output, err = public.ExecShell('ping6 -c 1 -W 1 ::1 2>/dev/null')
        if output and '1 received' in output:
            return True
    except:
        pass

    return False


def check_run():
    try:
        cfile = '/etc/ntp.conf'
        if not os.path.exists(cfile):
            return True, 'No risk'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        miss = []

        # IPv4 configuration must exist
        if not re.search(r'^\s*(?!#)\s*restrict\s+-4\s+default.*\bnoquery\b', conf, re.M):
            miss.append('Missing restrict -4 default configuration')

        # IPv6 configuration only checked when IPv6 is enabled
        ipv6_enabled = check_ipv6_enabled()
        if ipv6_enabled:
            if not re.search(r'^\s*(?!#)\s*restrict\s+-6\s+default.*\bnoquery\b', conf, re.M):
                miss.append('Missing restrict -6 default configuration')

        if not re.findall(r'^\s*(?!#)\s*server\s+\S+', conf, re.M):
            miss.append('Missing server line (/etc/ntp.conf)')

        syscfg = '/etc/sysconfig/ntpd'
        unitf = '/usr/lib/systemd/system/ntpd.service'
        if os.path.exists(syscfg):
            s = public.readFile(syscfg) or ''
            if '-u ntp:ntp' not in s:
                miss.append('ntpd not running as ntp user (missing -u ntp:ntp)')
        elif os.path.exists(unitf):
            s = public.readFile(unitf) or ''
            if '-u ntp:ntp' not in s:
                miss.append('ntpd not running as ntp user (missing -u ntp:ntp)')

        if miss:
            return False, 'NTP configuration is not standard: {}'.format(','.join(miss))
        return True, 'No risk'
    except:
        return True, 'No risk'
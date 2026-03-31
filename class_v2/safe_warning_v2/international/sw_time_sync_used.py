import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure time synchronization is used'
_version = 1.0
_ps = 'Check if time synchronization is enabled (ntp/chrony/timesyncd)'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_time_sync_used.pl")
_tips = [
    'Install and configure ntp or chrony on systems with time synchronization not enabled',
    'ntp example: yum install ntp or apt-get install ntp; configure server line in /etc/ntp.conf',
    'chrony example: yum install chrony or apt-get install chrony; configure server line in /etc/chrony.conf'
]
_help = ''
_remind = 'System time should be synchronized across all systems in the environment. This is typically done by establishing an authoritative time server or set of servers and having all systems synchronize their clocks to them.\nTime synchronization is important for supporting time-sensitive security mechanisms such as Kerberos, and also ensures log files have consistent time records throughout the enterprise, helping with forensic investigations.'


def check_run():
    try:
        used = False
        if os.path.exists('/etc/ntp.conf'):
            conf = public.readFile('/etc/ntp.conf') or ''
            if re.findall(r'^\s*(?!#)\s*server\s+\S+', conf, re.M):
                used = True
        for f in ['/etc/chrony.conf', '/etc/chrony/chrony.conf']:
            if os.path.exists(f):
                conf = public.readFile(f) or ''
                if re.findall(r'^\s*(?!#)\s*server\s+\S+', conf, re.M):
                    used = True
                    break
        tsf = '/etc/systemd/timesyncd.conf'
        if os.path.exists(tsf):
            conf = public.readFile(tsf) or ''
            if re.search(r'^\s*(?!#)\s*NTP\s*=\s*\S+', conf, re.M):
                used = True
        if not used:
            return False, 'Time synchronization not configured'
        return True, 'No risk'
    except:
        return True, 'No risk'
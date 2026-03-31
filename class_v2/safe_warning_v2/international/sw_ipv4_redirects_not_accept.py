import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure ICMP redirects are not accepted'
_version = 1.0
_ps = 'Check if IPv4 ICMP redirects are rejected'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_redirects_not_accept.pl")
_tips = [
    "Add to `/etc/sysctl.conf`:",
    "net.ipv4.conf.all.accept_redirects = 0",
    "net.ipv4.conf.default.accept_redirects = 0",
    "Execute: `sysctl -w net.ipv4.conf.all.accept_redirects=0`",
    "Execute: `sysctl -w net.ipv4.conf.default.accept_redirects=0`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`"
]
_help = ''
_remind = 'Attackers may use forged ICMP redirect messages to maliciously change the system routing table and allow them to send packets to incorrect networks and enable capture of system packets.'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.accept_redirects\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.accept_redirects\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, 'No risk'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.accept_redirects')
        if not k2: miss.append('net.ipv4.conf.default.accept_redirects')
        return False, 'IPv4 ICMP redirect not disabled in /etc/sysctl.conf: {}'.format(','.join(miss))
    except:
        return True, 'No risk'
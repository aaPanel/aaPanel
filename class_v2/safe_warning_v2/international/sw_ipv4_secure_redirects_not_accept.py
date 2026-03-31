import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure secure ICMP redirects are not accepted'
_version = 1.0
_ps = 'Check if secure ICMP redirects are rejected'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_secure_redirects_not_accept.pl")
_tips = [
    "Add to `/etc/sysctl.conf`:",
    "net.ipv4.conf.all.secure_redirects = 0",
    "net.ipv4.conf.default.secure_redirects = 0",
    "Execute: `sysctl -w net.ipv4.conf.all.secure_redirects=0`",
    "Execute: `sysctl -w net.ipv4.conf.default.secure_redirects=0`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`"
]
_help = ''
_remind = 'Secure ICMP redirects are the same as ICMP redirects, unless they come from gateways listed in the default gateway list. Assume these gateways are known to your system and they may be secure. Even known gateways may still be compromised. Setting net.ipv4.conf.all.secure_redirects to 0 protects the system from routing table updates that may have been compromised by known gateways.'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.secure_redirects\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.secure_redirects\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, 'No risk'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.secure_redirects')
        if not k2: miss.append('net.ipv4.conf.default.secure_redirects')
        return False, 'Secure ICMP redirects not disabled: {}'.format(','.join(miss))
    except:
        return True, 'No risk'
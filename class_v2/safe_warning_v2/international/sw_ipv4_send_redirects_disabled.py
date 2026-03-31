import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure packet redirect sending is disabled (host only)'
_version = 1.0
_ps = 'Check if IPv4 send redirects is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_send_redirects_disabled.pl")
_tips = [
    "Add to `/etc/sysctl.conf`:",
    "net.ipv4.conf.all.send_redirects = 0",
    "net.ipv4.conf.default.send_redirects = 0",
    "Execute: `sysctl -w net.ipv4.conf.all.send_redirects=0`",
    "Execute: `sysctl -w net.ipv4.conf.default.send_redirects=0`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`"
]
_help = ''
_remind = 'ICMP redirects are used to send routing information to other hosts. Since the host itself does not act as a router (in host-only configuration), there is no need to send redirects. If the server is used as a Docker host, please ignore this item.\nAttackers can use infected hosts to send invalid ICMP redirects to other router devices to try to compromise routing and make users access invalid systems set up by attackers.'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.send_redirects\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.send_redirects\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, 'No risk'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.send_redirects')
        if not k2: miss.append('net.ipv4.conf.default.send_redirects')
        return False, 'IPv4 redirect sending not disabled in /etc/sysctl.conf: {}'.format(','.join(miss))
    except:
        return True, 'No risk'
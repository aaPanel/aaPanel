import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure source routed packets are not accepted'
_version = 1.0
_ps = 'Check if source routed packets are disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_accept_source_route_disabled.pl")
_tips = [
    "Add to `/etc/sysctl.conf`:",
    "net.ipv4.conf.all.accept_source_route = 0",
    "net.ipv4.conf.default.accept_source_route = 0",
    "Execute: `sysctl -w net.ipv4.conf.all.accept_source_route=0`",
    "Execute: `sysctl -w net.ipv4.conf.default.accept_source_route=0`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`"
]
_help = ''
_remind = 'Setting net.ipv4.conf.all.accept_source_route and net.ipv4.conf.default.accept_source_route to 0 will prohibit the system from accepting source routed packets. Assume the system is capable of routing packets to an Internet-routable address on one interface and a private address on another interface. Assume the private address is not routable to the Internet and vice versa. In a normal routing environment, an attacker from an Internet-routable address cannot use the system as a way to reach private address systems. However, if source routed packets are allowed, they can be used to access private address systems because the route can be specified, rather than relying on routing protocols that do not allow this route.'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, 'No risk'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.accept_source_route')
        if not k2: miss.append('net.ipv4.conf.default.accept_source_route')
        return False, 'Source route not disabled in /etc/sysctl.conf: {}'.format(','.join(miss))
    except:
        return True, 'No risk'
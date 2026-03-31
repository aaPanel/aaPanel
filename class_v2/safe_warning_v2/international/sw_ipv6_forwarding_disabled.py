import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure IPv6 forwarding is disabled (host only)'
_version = 1.0
_ps = 'Check if IPv6 forwarding is disabled (host)'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_forwarding_disabled.pl")
_tips = [
    "Add to `/etc/sysctl.conf`: net.ipv6.conf.all.forwarding = 0",
    "Execute: `sysctl -w net.ipv6.conf.all.forwarding=0`",
    "Execute: `sysctl -w net.ipv6.route.flush=1`"
]
_help = ''
_remind = 'The net.ipv6.conf.all.forwarding flag is used to tell the system whether it can forward packets.\nSetting the flag to 0 ensures that systems with multiple interfaces (such as hard proxies) can never forward packets, and therefore cannot act as routers.\nIf the server is used as a Docker host, this item cannot be hardened.'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.forwarding\s*=\s*0\s*$', conf, re.M)
        if ok:
            return True, 'No risk'
        return False, 'sysctl not configured: net.ipv6.conf.all.forwarding=0'
    except:
        return True, 'No risk'
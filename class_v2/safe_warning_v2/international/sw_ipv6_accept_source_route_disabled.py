import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure IPv6 source routed packets are not accepted'
_version = 2.0
_ps = 'Check if IPv6 source routed packets are rejected (only detected when IPv6 is enabled)'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_accept_source_route_disabled.pl")
_tips = [
    "Add to `/etc/sysctl.conf`:",
    "net.ipv6.conf.all.accept_source_route = 0",
    "net.ipv6.conf.default.accept_source_route = 0",
    "Execute: `sysctl -w net.ipv6.conf.all.accept_source_route=0`",
    "Execute: `sysctl -w net.ipv6.conf.default.accept_source_route=0`",
    "Execute: `sysctl -w net.ipv6.route.flush=1`"
]
_help = ''
_remind = 'Prevents source routed packets from bypassing IPv6 network policies'


def is_ipv6_enabled():
    """Check if IPv6 is enabled"""
    # 检查是否禁用了IPv6模块
    dirs = ['/etc/modprobe.d']
    pat = re.compile(r'^\s*(?!#)\s*options\s+ipv6\s+disable\s*=\s*1\s*$', re.M)
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if not name.endswith('.conf'):
                continue
            fp = os.path.join(d, name)
            body = public.readFile(fp) or ''
            if pat.search(body):
                return False  # IPv6 disabled

    # 检查是否有IPv6地址
    try:
        if os.path.exists('/proc/net/if_inet6'):
            content = public.readFile('/proc/net/if_inet6')
            if content and content.strip():
                return True  # IPv6 enabled
    except:
        pass

    return False  # Default认为IPv6未启用


def check_run():
    try:
        # 如果IPv6未启用，跳过检测
        if not is_ipv6_enabled():
            return True, 'IPv6 is not enabled, skipping detection'

        # IPv6启用，检查是否禁用了源路由
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.default\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, 'No risk'
        miss = []
        if not k1: miss.append('net.ipv6.conf.all.accept_source_route')
        if not k2: miss.append('net.ipv6.conf.default.accept_source_route')
        return False, 'IPv6 source route not disabled in /etc/sysctl.conf: {}'.format(','.join(miss))
    except:
        return True, 'No risk'

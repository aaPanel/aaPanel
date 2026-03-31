import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure IPv6 router advertisements are not accepted'
_version = 2.0
_ps = 'Check if IPv6 router advertisements are disabled (only detected when IPv6 is enabled)'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_accept_ra_disabled.pl")
_tips = [
    "Add to `/etc/sysctl.conf`:",
    "net.ipv6.conf.all.accept_ra = 0",
    "net.ipv6.conf.default.accept_ra = 0",
    "Execute: `sysctl -w net.ipv6.conf.all.accept_ra=0`",
    "Execute: `sysctl -w net.ipv6.conf.default.accept_ra=0`",
    "Execute: `sysctl -w net.ipv6.route.flush=1`"
]
_help = ''
_remind = 'This setting disables the systems ability to accept IPv6 router advertisements. It is recommended that systems not accept router advertisements as they could be spoofed and route traffic to compromised computers.\nSetting hard routes within the system (usually a single default route to a trusted router) protects the system from erroneous routes'


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
                return False  # IPv6被禁用

    # 检查是否有IPv6地址
    try:
        if os.path.exists('/proc/net/if_inet6'):
            content = public.readFile('/proc/net/if_inet6')
            if content and content.strip():
                return True  # 有IPv6地址，说明IPv6启用
    except:
        pass

    return False  # 默认认为IPv6未启用


def check_run():
    try:
        # 如果IPv6未启用，跳过检测
        if not is_ipv6_enabled():
            return True, 'IPv6 is not enabled, skipping detection'

        # IPv6启用，检查是否禁用了路由器通告
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_ra\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.default\.accept_ra\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, 'No risk'
        miss = []
        if not k1: miss.append('net.ipv6.conf.all.accept_ra')
        if not k2: miss.append('net.ipv6.conf.default.accept_ra')
        return False, 'IPv6 router advertisement not disabled in /etc/sysctl.conf: {}'.format(','.join(miss))
    except:
        return True, 'No risk'

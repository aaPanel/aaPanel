import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'IPv6 security configuration detection'
_version = 2.0
_ps = 'Check if IPv6 configuration is secure (not disabled, but ensures secure settings)'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_disabled.pl")
_tips = [
    "If IPv6 is not needed, add to `/etc/modprobe.d/disable_ipv6.conf`: options ipv6 disable=1",
    "If using IPv6, it is recommended to configure the following security parameters:",
    "  net.ipv6.conf.all.accept_ra=0 (disable router advertisements)",
    "  net.ipv6.conf.all.accept_redirects=0 (disable redirects)",
]
_help = ''
_remind = 'IPv6 is a modern network protocol, and it is not recommended to force disable it. If using IPv6, ensure security parameters are configured to reduce the attack surface.'


def check_run():
    """
    Check IPv6 configuration security
    1. If IPv6 is disabled -> No risk
    2. If IPv6 is enabled but security parameters are configured -> No risk
    3. If IPv6 is enabled and security parameters are not configured -> Risk warning
    """
    try:
        # 检查IPv6是否被禁用
        dirs = ['/etc/modprobe.d']
        pat = re.compile(r'^\s*(?!#)\s*options\s+ipv6\s+disable\s*=\s*1\s*$', re.M)
        ipv6_disabled = False
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                if not name.endswith('.conf'):
                    continue
                fp = os.path.join(d, name)
                body = public.readFile(fp) or ''
                if pat.search(body):
                    ipv6_disabled = True
                    break
            if ipv6_disabled:
                break

        # 如果IPv6已禁用，无风险
        if ipv6_disabled:
            return True, 'IPv6 is disabled, no risk'

        # IPv6未禁用，检查是否配置了安全参数
        conf = public.readFile('/etc/sysctl.conf') or ''

        # 检查关键IPv6安全参数
        accept_ra = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_ra\s*=\s*0\s*$', conf, re.M)
        accept_redirects = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_redirects\s*=\s*0\s*$', conf, re.M)

        # 如果配置了安全参数，无风险
        if accept_ra and accept_redirects:
            return True, 'IPv6 is enabled and security parameters are configured, no risk'

        # IPv6启用但未配置安全参数，提示建议
        miss = []
        if not accept_ra:
            miss.append('net.ipv6.conf.all.accept_ra=0')
        if not accept_redirects:
            miss.append('net.ipv6.conf.all.accept_redirects=0')

        return False, 'IPv6 is enabled but security parameters are not configured, it is recommended to set: {}'.format(', '.join(miss))
    except:
        return True, 'No risk'

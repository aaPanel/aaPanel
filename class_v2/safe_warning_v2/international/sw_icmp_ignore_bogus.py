import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure bogus ICMP responses are ignored'
_version = 1.0
_ps = 'Check if bogus ICMP error responses are ignored'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_icmp_ignore_bogus.pl")
_tips = [
    "Add in `/etc/sysctl.conf`: net.ipv4.icmp_ignore_bogus_error_responses = 1",
    "Execute: `sysctl -w net.ipv4.icmp_ignore_bogus_error_responses=1`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`",
]
_help = ''
_remind = 'Setting icmp_ignore_bogus_error_responses to 1 prevents the kernel from logging虚假responses from broadcast remapping, which prevents the filesystem from filling with useless log messages.\nSome routers (and some attackers) send RFC-1122-incompatible responses in violation, attempting to fill the log filesystem with many useless error messages.'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv4\.icmp_ignore_bogus_error_responses\s*=\s*1\s*$', conf, re.M)
        if ok:
            return True, 'No risk'
        return False, 'sysctl not configured: net.ipv4.icmp_ignore_bogus_error_responses=1'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure suspicious packets are logged'
_version = 1.0
_ps = 'Enable suspicious packet logging (log_martians)'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_log_martians_enabled.pl")
_tips = [
    "Add to `/etc/sysctl.conf`:",
    "net.ipv4.conf.all.log_martians = 1",
    "net.ipv4.conf.default.log_martians = 1",
    "Execute: `sysctl -w net.ipv4.conf.all.log_martians=1`",
    "Execute: `sysctl -w net.ipv4.conf.default.log_martians=1`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`"
]
_help = ''
_remind = 'Logging unroutable source packets improves visibility and traceability capabilities'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.log_martians\s*=\s*1\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.log_martians\s*=\s*1\s*$', conf, re.M)
        if k1 and k2:
            return True, 'No risk'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.log_martians')
        if not k2: miss.append('net.ipv4.conf.default.log_martians')
        return False, 'Suspicious packet logging not enabled: {}'.format(','.join(miss))
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure SSH LogLevel is set to INFO'
_version = 1.0
_ps = 'Check if SSH LogLevel is set to INFO/VERBOSE'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_loglevel.pl")
_tips = [
    "Edit /etc/ssh/sshd_config file and set the parameter as follows:",
    "LogLevel VERBOSE or LogLevel INFO",
    "Restart sshd: systemctl restart sshd",
]
_help = ''
_remind = 'Ensure SSH LogLevel is set to INFO, log login and logout activities, improve auditing and traceability'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        matches = re.findall(r'^\s*(?!#)\s*LogLevel\s+(\S+)', conf, re.M)
        if not matches:
            return True, 'No risk'
        val = matches[-1].split('#')[0].strip().strip('"').strip("'")
        v = val.lower()
        if v not in ('info', 'verbose'):
            return False, 'LogLevel is not set to INFO or VERBOSE'
        return True, 'No risk'
    except:
        return True, 'No risk'
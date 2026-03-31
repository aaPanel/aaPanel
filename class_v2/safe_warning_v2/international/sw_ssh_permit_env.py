import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure SSH PermitUserEnvironment is disabled'
_version = 1.0
_ps = 'Check if SSH PermitUserEnvironment is disabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_permit_env.pl")
_tips = [
    "Edit `/etc/ssh/sshd_config` and set PermitUserEnvironment to no:",
    "PermitUserEnvironment no",
    "Then restart SSH service",
]
_help = ''
_remind = 'The ability to allow users to set environment variables through the ssh daemon may allow users to bypass security controls (e.g., setting execution paths with ssh executing Trojan horse programs)'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        matches = re.findall(r'^\s*(?!#)\s*PermitUserEnvironment\s+(.+)$', conf, re.M)
        if not matches:
            return False, 'PermitUserEnvironment is not disabled'
        val = matches[-1].split('#')[0].strip().strip('"').strip("'")
        v = val.lower()
        if v in ('yes', 'on', 'true'):
            return False, 'PermitUserEnvironment is not disabled'
        if v != 'no':
            return False, 'PermitUserEnvironment is not disabled'
        return True, 'No risk'
    except:
        return True, 'No risk'
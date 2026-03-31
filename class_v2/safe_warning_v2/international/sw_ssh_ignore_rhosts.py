import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure SSH IgnoreRhosts is enabled'
_version = 1.0
_ps = 'Check if SSH IgnoreRhosts is enabled'
_level = 1
_date = '2025-11-18'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_ignore_rhosts.pl")
_tips = [
    "Edit `/etc/ssh/sshd_config` and set `IgnoreRhosts` to: yes",
    "Then restart SSH service systemctl restart sshd",
]
_help = ''
_remind = 'The IgnoreRhosts parameter specifies that .rhosts and .shosts files will not be used in RhostsRSAAuthentication or HostbasedAuthentication.\nSetting this parameter will force users to enter passwords when authenticating using ssh.'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        values = re.findall(r'^\s*(?!#)\s*IgnoreRhosts\s+(\S+)', conf, re.M)
        if not values:
            return True, 'No risk'
        val = values[-1].strip().lower()
        if val in ('yes', 'on', 'true'):
            return True, 'No risk'
        return False, 'IgnoreRhosts is not enabled'
    except:
        return True, 'No risk'
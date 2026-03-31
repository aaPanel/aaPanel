import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure only approved MAC algorithms are used'
_version = 1.0
_ps = 'Check if only approved SSH MAC algorithms are enabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_macs.pl")
_tips = [
    "Edit /etc/ssh/sshd_config file and set the following parameters, then restart SSH service:",
    "MACs hmac-sha2-512,hmac-sha2-256",
]
_help = ''
_remind = 'MD5 and 96-bit MAC algorithms are considered weak and have been shown to improve the exploitability of ssh downgrade attacks.\nThis variable restricts the types of MAC algorithms that SSH can use during communication.'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        matches = re.findall(r'^\s*(?!#)\s*MACs\s+(.+)$', conf, re.M)
        if not matches:
            return True, 'No risk'
        line = matches[-1].split('#')[0].strip()
        vals = [v.strip().lower() for v in line.replace('"', '').replace("'", '').split(',') if v.strip()]
        allowed = {'hmac-sha2-512', 'hmac-sha2-256'}
        extra = [v for v in vals if v not in allowed]
        if extra:
            return False, 'Non-approved MAC algorithms exist: {}'.format(','.join(extra))
        return True, 'No risk'
    except:
        return True, 'No risk'
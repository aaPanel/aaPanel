import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure local login warning banner is configured correctly'
_version = 1.0
_ps = 'Check if local login banner is cleaned'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_local_login_banner.pl")
_tips = [
    "Edit `/etc/issue` and remove `\\m`, `\\r`, `\\s`, `\\v` configurations",
    "Fill in unified warning content according to site policy, for example:",
    "echo \"Authorized uses only. All activity may be monitored and reported.\" > /etc/issue",
]
_help = ''
_remind = 'Displaying OS and patch level information in warning messages provides detailed system information to attackers trying to exploit specific system vulnerabilities.'


def check_run():
    try:
        cfile = '/etc/issue'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        bad = set(re.findall(r'(\\[mrsv])', conf))
        if bad:
            return False, 'Local login banner contains system information variables: {}'.format(','.join(sorted(bad)))
        return True, 'No risk'
    except:
        return True, 'No risk'
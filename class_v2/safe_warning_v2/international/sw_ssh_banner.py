import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure SSH warning notification is configured'
_version = 1.1
_ps = 'Check if SSH login warning is set'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_banner.pl")
_tips = [
    "Edit `/etc/ssh/sshd_config` file and set Banner path, then restart SSH service:",
    "Banner /etc/issue.net or /etc/issue or other custom path",
]
_help = ''
_remind = 'The Banner parameter specifies a file whose contents must be sent to the remote user before authentication is allowed.\nDisplaying a warning message before normal user login may help warn intruders on the computer system.'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        matches = re.findall(r'^\s*(?!#)\s*Banner\s+(.+)$', conf, re.M)
        if not matches:
            return False, 'Banner is not set or set to none'
        val = matches[-1].split('#')[0].strip().strip('"').strip("'")
        v = val.lower()
        if v in ('none', ''):
            return False, 'SSH warning notification is not set'

        # Changed to: as long as Banner is set and the file exists, no restriction on specific path
        if os.path.exists(val):
            return True, 'No risk'
        else:
            return False, 'Banner file does not exist: {}'.format(val)
    except:
        return True, 'No risk'
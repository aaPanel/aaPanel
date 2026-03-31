import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure no legacy "+" entries exist in /etc/passwd'
_version = 1.0
_ps = 'Check if /etc/passwd has legacy "+" entries'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_passwd_legacy_plus.pl")
_tips = [
    "Backup: `cp -a /etc/passwd /etc/passwd.bak.$(date +%F)`",
    "Clean: `sed -i '/^\\s*\\+/d' /etc/passwd`"
]
_help = ''
_remind = 'The + character in various files was once a system marker used to insert data from NIS maps at a certain point in system configuration files. Most systems no longer need these entries, but they may exist in files imported from other platforms. These entries may provide a way for attackers to gain privileged access to the system.'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, 'No risk'
        hits = re.findall(r'^\s*\+.*$', body, re.M)
        if hits:
            return False, 'Legacy "+" entries exist in /etc/passwd: {} items'.format(len(hits))
        return True, 'No risk'
    except:
        return True, 'No risk'
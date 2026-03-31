import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure UDF filesystem mount is disabled'
_version = 1.0
_ps = 'Check if UDF filesystem module is disabled'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_udf_disabled.pl")
_tips = [
    'Create or edit /etc/modprobe.d/CIS.conf and add: install udf /bin/true'
]
_help = ''
_remind = 'The UDF filesystem type is a Universal Disk Format used to implement ISO/IEC 13346 and ECMA-167 specifications. It is an open vendor filesystem type used for data storage on various media. This filesystem type is required for supporting writable DVD and optical disc formats. Removing support for unnecessary filesystem types reduces the systems local attack surface.\nIf this filesystem type is not needed, disable it.'


def check_run():
    try:
        d = '/etc/modprobe.d'
        if not os.path.isdir(d):
            return True, 'No risk'
        for name in os.listdir(d):
            if not name.endswith('.conf'):
                continue
            fp = os.path.join(d, name)
            body = public.readFile(fp) or ''
            if re.search(r'^\s*(?!#)\s*install\s+udf\s+/bin/true\s*$', body, re.M):
                return True, 'No risk'
        return False, 'Disable rule not configured in /etc/modprobe.d/*.conf: install udf /bin/true'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure gpgcheck is globally activated'
_version = 1.0
_ps = 'Check if YUM package signature verification is enabled'
_level = 2
_date = '2025-11-22'
_ignore = os.path.exists("data/warning/ignore/sw_yum_gpgcheck_enabled.pl")
_tips = [
    'Set in `[main]` section of `/etc/yum.conf`: gpgcheck=1',
    'Set all `gpgcheck` instances to 1 in `/etc/yum.repos.d/*.repo`: sed -ri "s/^[[:space:]]*gpgcheck[[:space:]]*=.*/gpgcheck=1/" /etc/yum.repos.d/*.repo'
]
_help = ''
_remind = 'The gpgcheck option found in the main section of /etc/yum.conf and individual /etc/yum/repos.d/* files determines whether RPM package signatures are checked before installation.\nAlways ensure RPM package signatures are checked before installation to ensure software is obtained from trusted sources.'


def check_run():
    try:
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'
        issues = []
        yum_conf = '/etc/yum.conf'
        conf = public.readFile(yum_conf) or ''
        main_g = None
        if conf:
            for m in re.findall(r'^\s*(?!#)\s*gpgcheck\s*=\s*(\S+)\s*$', conf, re.M):
                main_g = m.strip()
                break
            if main_g != '1':
                issues.append('/etc/yum.conf [main] gpgcheck=1 not enabled')
        repos_dir = '/etc/yum.repos.d'
        if os.path.isdir(repos_dir):
            for name in os.listdir(repos_dir):
                if not name.endswith('.repo'):
                    continue
                fp = os.path.join(repos_dir, name)
                body = public.readFile(fp) or ''
                for m in re.findall(r'^\s*(?!#)\s*gpgcheck\s*=\s*(\S+)\s*$', body, re.M):
                    if m.strip() != '1':
                        issues.append('{} gpgcheck=1 not enabled'.format(fp))
        if issues:
            return False, 'gpgcheck not globally enabled: {}'.format('、'.join(issues))
        return True, 'No risk'
    except:
        return True, 'No risk'
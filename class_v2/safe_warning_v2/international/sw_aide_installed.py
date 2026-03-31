import sys, os, shutil
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure AIDE is installed'
_version = 1.0
_ps = 'Check if AIDE is installed'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_aide_installed.pl")
_tips = [
    'Debian/Ubuntu installation: apt-get install aide && aideinit',
    'RHEL/CentOS installation: yum install aide && aide --init && mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz'
]
_help = ''
_remind = 'Without AIDE deployed, tampering of critical system files cannot be detected; after installation and initialization, it can provide file integrity auditing and alerts, reducing the risk of intrusion and accidental modification'


def check_run():
    try:
        if shutil.which('aide'):
            return True, 'No risk'
        bins = [
            '/usr/bin/aide',
            '/usr/sbin/aide',
            '/usr/local/bin/aide',
            '/usr/local/sbin/aide'
        ]
        found_exec = None
        for p in bins:
            try:
                if os.path.exists(p) and os.access(p, os.X_OK):
                    found_exec = p
                    break
            except:
                pass
        if found_exec:
            return True, 'No risk'
        rpm_ok = False
        dpkg_ok = False
        try:
            out, err = public.ExecShell('rpm -q aide')
            if out and ('aide' in out) and ('not installed' not in out.lower()):
                rpm_ok = True
        except:
            pass
        try:
            out, err = public.ExecShell('dpkg -s aide | grep Status')
            if out and ('install ok installed' in out):
                dpkg_ok = True
        except:
            pass
        if rpm_ok or dpkg_ok:
            return True, 'No risk'
        return False, 'AIDE not detected: No executable found (/usr/bin/aide,/usr/sbin/aide,/usr/local/bin/aide,/usr/local/sbin/aide), and rpm/dpkg query shows not installed'
    except:
        return True, 'No risk'
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure auditing of processes started prior to auditd is enabled'
_version = 2.0
_ps = 'Check if auditd process log auditing is enabled (only detected when auditd is installed)'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_early_enabled.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Edit `/etc/default/grub` and add `audit=1` to `GRUB_CMDLINE_LINUX`",
    "CentOS/RHEL: `grub2-mkconfig -o /boot/grub2/grub.cfg`",
    "Debian/Ubuntu: `update-grub`",
    "Legacy Grub: edit `/boot/grub/grub.conf` and append `audit=1` to all `kernel` lines"
]
_help = ''
_remind = 'Without enabling audit=1, processes started before auditd will not be audited; after enabling, system boot phase events will be covered, improving compliance and traceability capabilities'


def is_auditd_installed():
    """Check if auditd is installed"""
    if os.path.exists('/usr/sbin/auditd') or os.path.exists('/sbin/auditd'):
        return True
    try:
        if os.path.exists('/usr/bin/rpm'):
            result = os.popen('rpm -q audit 2>/dev/null').read()
            if result and 'audit' in result.lower() and 'not installed' not in result.lower():
                return True
        elif os.path.exists('/usr/bin/dpkg'):
            result = os.popen('dpkg -l auditd 2>/dev/null').read()
            if result and 'auditd' in result.lower() and 'no packages found' not in result.lower():
                return True
    except:
        pass
    return False


def check_run():
    try:
        # 首先检查auditd是否安装
        if not is_auditd_installed():
            return True, 'auditd is not installed, skipping detection'

        # auditd已安装，检查引导配置
        hits = []
        df = '/etc/default/grub'
        if os.path.exists(df):
            body = public.readFile(df) or ''
            ok1 = re.search(r'^\s*(?!#)\s*GRUB_CMDLINE_LINUX[^\n]*\baudit=1\b', body, re.M)
            ok2 = re.search(r'^\s*(?!#)\s*GRUB_CMDLINE_LINUX_DEFAULT[^\n]*\baudit=1\b', body, re.M)
            if ok1 or ok2:
                hits.append(df)
        cfgs = [
            '/boot/grub2/grub.cfg',
            '/etc/grub2.cfg',
            '/boot/grub/grub.cfg',
            '/boot/grub/grub.conf'
        ]
        checked_cfgs = []
        for fp in cfgs:
            if not os.path.exists(fp):
                continue
            body = public.readFile(fp) or ''
            if re.search(r'^\s*(linux|kernel)\b[^\n]*\baudit=1\b', body, re.M):
                hits.append(fp)
            checked_cfgs.append(fp)
        if hits:
            return True, 'No risk'
        parts = []
        if os.path.exists(df):
            parts.append('/etc/default/grub does not set audit=1 in GRUB_CMDLINE_LINUX/GRUB_CMDLINE_LINUX_DEFAULT\n')
        if checked_cfgs:
            parts.append('grub configuration (kernel/linux lines) does not enable audit=1: ' + ','.join(checked_cfgs))
        msg = 'audit=1 is not enabled in boot configuration' if not parts else ';'.join(parts)
        return False, msg
    except:
        return True, 'No risk'

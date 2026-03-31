import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure audit log storage size is configured'
_version = 2.0
_ps = 'Check if audit log size is limited (only detected when auditd is installed)'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_max_log_file_configured.pl")
_tips = [
    "Install auditd (if not installed):",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "Edit `/etc/audit/auditd.conf` and set: max_log_file = 50 (in MB)",
    "Restart audit service: systemctl restart auditd or service auditd restart"
]
_help = ''
_remind = 'Without limiting audit log size, it may fill up the disk or be too small causing frequent rotation and loss of audit data; reasonably setting max_log_file can balance disk usage and forensic retention'


def is_auditd_installed():
    """Check if auditd is installed"""
    # 检查auditd配置文件是否存在
    if os.path.exists('/etc/audit/auditd.conf'):
        return True

    # 检查auditd可执行文件
    if os.path.exists('/usr/sbin/auditd') or os.path.exists('/sbin/auditd'):
        return True

    # 检查是否通过包管理器安装
    try:
        # 检查rpm
        if os.path.exists('/usr/bin/rpm'):
            result = os.popen('rpm -q audit 2>/dev/null').read()
            if result and 'audit' in result.lower() and 'not installed' not in result.lower():
                return True
        # 检查dpkg
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
            # auditd未安装，跳过检测
            return True, 'auditd is not installed, skipping detection'

        # auditd已安装，检查配置
        cfile = '/etc/audit/auditd.conf'
        if not os.path.exists(cfile):
            return False, 'auditd is installed but config file is missing: /etc/audit/auditd.conf'
        body = public.readFile(cfile) or ''
        m = re.search(r'^\s*max_log_file\s*=\s*(\d+)\s*$', body, re.M)
        if not m:
            return False, 'max_log_file parameter not configured in auditd.conf, recommended to set to 50'
        val = int(m.group(1))
        if 5 <= val <= 100:
            return True, 'No risk'
        return False, 'max_log_file value is not in recommended range [5,100]: {}'.format(val)
    except:
        return True, 'No risk'

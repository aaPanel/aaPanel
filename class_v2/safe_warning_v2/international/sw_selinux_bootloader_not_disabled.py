import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure SELinux is not disabled in bootloader configuration'
_version = 1.0
_ps = 'Check if SELinux protection is removed'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_selinux_bootloader_not_disabled.pl")
_tips = [
    "Edit `/etc/default/grub` and remove `selinux=0`, `enforcing=0` from `GRUB_CMDLINE_LINUX*`",
    "CentOS/RHEL: grub2-mkconfig > /boot/grub2/grub.cfg",
    "Debian/Ubuntu: update-grub",
    "Legacy: edit `/boot/grub/grub.conf` and remove `selinux=0` and `enforcement=0`"
]
_help = ''
_remind = 'Configure SELinux to be enabled at boot and verify it is not overridden by grub boot parameters. SELinux must be enabled at boot in the grub configuration to ensure the controls it provides are not overridden.'


def check_run():
    try:
        files = [
            '/etc/default/grub',
            '/boot/grub2/grub.cfg',
            '/etc/grub2.cfg',
            '/boot/grub/grub.cfg',
            '/boot/grub/grub.conf'
        ]
        bad_tokens = ('selinux=0', 'enforcing=0', 'enforcement=0')
        hits = []
        for fp in files:
            if not os.path.exists(fp):
                continue
            body = public.readFile(fp) or ''
            for t in bad_tokens:
                if t in body:
                    hits.append(fp + ':' + t)
        if hits:
            return False, 'Boot config contains SELinux disable parameters: {}'.format(','.join(hits))
        return True, 'No risk'
    except:
        return True, 'No risk'
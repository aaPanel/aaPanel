import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = 'Ensure bootloader does not disable AppArmor'
_version = 1.0
_ps = 'Check if bootloader configuration contains settings to disable AppArmor'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_apparmor_bootloader_not_disabled.pl")
_tips = [
    "Edit `/etc/default/grub` and remove apparmor=0 from GRUB_CMDLINE_LINUX, GRUB_CMDLINE_LINUX_DEFAULT parameters",
    "Run `update-grub` to update configuration"
]
_help = ''
_remind = 'Configure AppArmor to be enabled at boot and verify it is not overridden by boot loader boot parameters. AppArmor must be enabled at boot in the boot loader configuration to ensure the controls it provides are not overridden.'


def check_run():
    try:
        # 只检测ubuntu系统
        if not isUbuntu():
            return True, 'No risk'

        files = [
            '/etc/default/grub',
            '/boot/grub2/grub.cfg',
            '/etc/grub2.cfg',
            '/boot/grub/grub.cfg',
            '/boot/grub/grub.conf'
        ]
        for fp in files:
            if not os.path.exists(fp):
                continue
            body = public.readFile(fp) or ''
            if 'apparmor=0' in body:
                return False, 'Boot config file {} contains AppArmor disable parameter: {}'.format(fp, 'apparmor=0')
        return True, 'No risk'
    except:
        return True, 'No risk'

def isUbuntu(self):
    try:
        if os.path.exists('/etc/lsb-release'):
            body = public.readFile('/etc/lsb-release') or ''
            if 'DISTRIB_ID=Ubuntu' in body:
                return True
        return False
    except:
        return False
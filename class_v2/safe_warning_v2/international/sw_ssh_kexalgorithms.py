import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure strong key exchange algorithms are used'
_version = 1.0
_ps = 'Check if strong key exchange algorithms are enabled'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_kexalgorithms.pl")
_tips = [
    "Edit /etc/ssh/sshd_config file, add/modify the kexalgorithms line to contain a comma-separated list of site-approved strong key exchange algorithms:",
    "KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group-exchange-sha256",
    "Restart sshd: systemctl restart sshd",
]
_help = ''
_remind = 'Key exchange is any method in cryptography by which secret keys are exchanged between two parties, allowing the use of cryptographic algorithms.\nIf the sender and receiver wish to exchange encrypted messages, each must be equipped to encrypt messages to be sent and decrypt messages received'


def check_run():
    try:
        if not os.path.exists('/etc/centos-release'):
            return True, 'No risk'

        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        matches = re.findall(r'^\s*(?!#)\s*KexAlgorithms\s+(.+)$', conf, re.M)
        if not matches:
            return True, 'No risk'
        line = matches[-1].split('#')[0].strip()
        vals = [v.strip().lower() for v in line.replace('"', '').replace("'", '').split(',') if v.strip()]
        allowed = {
            'curve25519-sha256',
            'curve25519-sha256@libssh.org',
            'diffie-hellman-group14-sha256',
            'diffie-hellman-group16-sha512',
            'diffie-hellman-group18-sha512',
            'ecdh-sha2-nistp521',
            'ecdh-sha2-nistp384',
            'ecdh-sha2-nistp256',
            'diffie-hellman-group-exchange-sha256',
        }
        extra = [v for v in vals if v not in allowed]
        if extra:
            return False, 'Non-approved key exchange algorithms exist: {}'.format(','.join(extra))
        return True, 'No risk'
    except:
        return True, 'No risk'
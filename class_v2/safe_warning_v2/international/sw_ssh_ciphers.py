import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure only approved ciphers are used'
_version = 1.1
_ps = 'Check if approved SSH cipher algorithms are enabled'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_ciphers.pl")
_tips = [
    "Edit `/etc/ssh/sshd_config` file and set the following parameters, then restart SSH service:",
    "Ciphers aes256-gcm@openssh.com,aes128-gcm@openssh.com,chacha20-poly1305@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr",
]
_help = ''
_remind = 'This variable limits the types of ciphers that SSH can use during communication, preventing connections from being downgraded and cracked'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, 'No risk'
        matches = re.findall(r'^\s*(?!#)\s*Ciphers\s+(.+)$', conf, re.M)
        if not matches:
            return True, 'No risk'
        line = matches[-1].strip()
        line = line.split('#')[0].strip()
        vals = [v.strip().lower() for v in line.replace('"', '').replace("'", '').split(',') if v.strip()]

        # Extended allowed algorithms (reference CIS Benchmark 2024)
        allowed = {
            'aes256-gcm@openssh.com',  # GCM mode (more secure, AEAD encryption)
            'aes128-gcm@openssh.com',
            'aes256-ctr',
            'aes192-ctr',
            'aes128-ctr',
            'chacha20-poly1305@openssh.com'  # ChaCha20-Poly1305 (suitable for mobile devices)
        }

        # Weak algorithm list (need to report risk)
        weak_algos = {
            'arcfour', 'arcfour128', 'arcfour256', 'arcfour512',
            'blowfish-cbc', 'blowfish',
            'cast128-cbc', 'cast128',
            '3des-cbc', '3des', 'des',
            'rijndael-cbc', 'rijndael',
            'serpent256-cbc',
            'cast128-cbc',
            'aes192-cbc', 'aes256-cbc', 'aes128-cbc'  # CBC mode is not as good as CTR/GCM
        }

        # Check for weak algorithms
        has_weak = False
        weak_list = []
        for v in vals:
            if v in weak_algos or any(w in v for w in weak_algos):
                has_weak = True
                weak_list.append(v)

        if has_weak:
            return False, 'Weak cipher algorithms detected (recommended to replace with GCM/CTR mode): {}'.format(','.join(weak_list))

        # Check for non-recommended algorithms
        extra = [v for v in vals if v not in allowed]
        if extra:
            # Non-weak but not recommended algorithms, only prompt without error
            return True, 'No risk (Tip: Non-recommended algorithms exist: {}, recommended to use: aes256-gcm@openssh.com,aes128-gcm@openssh.com,chacha20-poly1305@openssh.com,aes256-ctr,aes128-ctr)'.format(','.join(extra))

        return True, 'No risk'
    except:
        return True, 'No risk'
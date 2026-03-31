import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure ICMP broadcasts are ignored'
_version = 1.0
_ps = 'Check if ICMP broadcast echo requests are ignored'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_icmp_echo_ignore_broadcasts.pl")
_tips = [
    "Add in `/etc/sysctl.conf`: net.ipv4.icmp_echo_ignore_broadcasts = 1",
    "Execute: `sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`"
]
_help = ''
_remind = 'Setting net.ipv4.icmp_echo_ignore_broadcasts to 1 will cause the system to ignore all ICMP echo and timestamp requests to broadcast and multicast addresses. Accepting ICMP echo and timestamp requests with network broadcast or multicast destinations can be used to trick hosts into initiating (or participating in) Smurf attacks. The Smurf attack relies on the attacker sending large amounts of ICMP broadcast messages with a spoofed source address. All hosts receiving this message and responding will send echo-reply messages back to the spoofed address, which may be unreachable. If many hosts respond, traffic on the network can increase significantly.'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv4\.icmp_echo_ignore_broadcasts\s*=\s*1\s*$', conf, re.M)
        if ok:
            return True, 'No risk'
        return False, 'sysctl not configured: net.ipv4.icmp_echo_ignore_broadcasts=1'
    except:
        return True, 'No risk'
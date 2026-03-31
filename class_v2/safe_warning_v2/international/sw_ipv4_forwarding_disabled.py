import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'Ensure IP forwarding is disabled (host only)'
_version = 1.1
_ps = 'Check if IPv4 forwarding is disabled'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_forwarding_disabled.pl")
_tips = [
    "Add to `/etc/sysctl.conf`: net.ipv4.ip_forward = 0",
    "Execute: `sysctl -w net.ipv4.ip_forward=0`",
    "Execute: `sysctl -w net.ipv4.route.flush=1`"
]
_help = ''
_remind = 'If the server is used as a Docker host, please ignore this item. Setting the flag to 0 ensures that systems with multiple interfaces (such as hard proxies) can never forward packets, and therefore cannot act as routers'


def check_container_env():
    '''Check if running in container or virtualization environment (requires IP forwarding)'''
    # 检查Docker
    if os.path.exists('/usr/bin/docker') or os.path.exists('/usr/bin/dockerd'):
        try:
            output, err = public.ExecShell('docker ps -q 2>/dev/null')
            if output.strip():
                return True
        except:
            pass
        # 检查Docker服务是否运行
        try:
            output, err = public.ExecShell('systemctl is-active docker 2>/dev/null')
            if 'active' in output or 'running' in output:
                return True
        except:
            pass

    # 检查containerd
    try:
        output, err = public.ExecShell('systemctl is-active containerd 2>/dev/null')
        if 'active' in output:
            return True
    except:
        pass

    # 检查Podman
    if os.path.exists('/usr/bin/podman'):
        try:
            output, err = public.ExecShell('podman ps -q 2>/dev/null')
            if output.strip():
                return True
        except:
            pass

    # 检查KVM/libvirt虚拟机
    if os.path.exists('/usr/bin/virsh'):
        try:
            output, err = public.ExecShell('virsh list 2>/dev/null | grep -c "running"')
            if output.strip() and int(output.strip()) > 0:
                return True
        except:
            pass

    # 检查容器相关内核模块
    try:
        modules, err = public.ExecShell('lsmod | grep -E "bridge|overlay|br_netfilter|nf_conntrack"')
        if modules.strip():
            return True
    except:
        pass

    return False


def check_run():
    try:
        # 检测容器/虚拟化环境，如果存在则跳过检测
        if check_container_env():
            return True, 'No risk (container/virtualization environment detected, IP forwarding required)'

        # 普通服务器才检测IP转发配置
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv4\.ip_forward\s*=\s*0\s*$', conf, re.M)
        if ok:
            return True, 'No risk'
        return False, 'Not set in /etc/sysctl.conf: net.ipv4.ip_forward=0'
    except:
        return True, 'No risk'
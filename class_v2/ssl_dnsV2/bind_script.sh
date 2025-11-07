#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_Bind()
{
    if command -v yum >/dev/null 2>&1; then
        # CentOS/RHEL
        echo "Detected yum, installing BIND..."
        yum install bind bind-chroot -y
        # chroot 环境配置
        mkdir -p /var/named/chroot/etc
        mkdir -p /var/named/chroot/var/named/data
        mkdir -p /var/named/chroot/var/named/dynamic

        if [ ! -f /var/named/chroot/etc/named.rfc1912.zones ];then
            if [ -d '/usr/share/doc/bind/sample/var/named/' ];then
              cp -R /usr/share/doc/bind/sample/var/named/* /var/named/chroot/var/named/
            else
              cp -R /usr/share/doc/bind-*/sample/var/named/* /var/named/chroot/var/named/
            fi
            # 复制所有配置文件
            echo "Configuring BIND for the first time..."
            cp -p /etc/named.* /var/named/chroot/etc/
            touch /var/named/chroot/var/named/data/cache_dump.db
            touch /var/named/chroot/var/named/data/named_stats.txt
            touch /var/named/chroot/var/named/data/named_mem_stats.txt
            touch /var/named/chroot/var/named/data/named.run
            touch /var/named/chroot/var/named/dynamic/managed-keys.bind
            # 修改默认值
            NAMED_CONF_PATH="/var/named/chroot/etc/named.conf"
            sed -i 's/listen-on port 53 .*/listen-on port 53 { any; };/' "$NAMED_CONF_PATH"
            sed -i 's/allow-query .*/allow-query     { any; };/' "$NAMED_CONF_PATH"
            sed -i 's/recursion yes;/recursion no;/' "$NAMED_CONF_PATH"
        fi

        # 设置权限
        chown -R named:named /var/named/chroot

        SERVICE_NAME="named"
        if systemctl list-unit-files | grep -q "named-chroot.service"; then
            SERVICE_NAME="named-chroot"
        fi

        systemctl disable pdns >/dev/null 2>&1
        systemctl stop pdns >/dev/null 2>&1
        systemctl restart "$SERVICE_NAME"
        systemctl enable "$SERVICE_NAME"
        echo "bind" > /www/server/panel/class_v2/ssl_dnsV2/aadns.pl
        echo "BIND installed and configured for CentOS/RHEL."
        echo "Installed Success!"

    elif command -v apt-get >/dev/null 2>&1; then
        # Debian/Ubuntu
        echo "Detected apt, installing BIND9..."
        apt-get update
        apt-get install bind9 bind9utils -y
        systemctl stop bind9

        # 创建用户组
        if ! getent group named >/dev/null; then groupadd named; fi
        if ! id -u named >/dev/null 2>&1; then useradd -g named -s /sbin/nologin -d /var/named named; fi

        # chroot 环境配置
        CHROOT_DIR="/var/named/chroot"
        mkdir -p "$CHROOT_DIR/etc"
        mkdir -p "$CHROOT_DIR/dev"
        mkdir -p "$CHROOT_DIR/var/named/data"
        mkdir -p "$CHROOT_DIR/var/named/dynamic"
        mkdir -p "$CHROOT_DIR/var/cache/bind"
        mkdir -p "$CHROOT_DIR/var/run/named"

        # 移动配置文件并创建符号链接
        if [ -d /etc/bind ] && [ ! -L /etc/bind ]; then
            mv /etc/bind "$CHROOT_DIR/etc/"
            ln -s "$CHROOT_DIR/etc/bind" /etc/bind
        fi

        # 以chroot模式启动
        if [ -f /etc/default/named ]; then
            # -u: user, -t: chroot directory
            sed -i "s/OPTIONS=.*/OPTIONS=\"-u named -t \/var\/named\/chroot\"/" /etc/default/named
        fi

        # chroot所需的设备文件
        if [ ! -c "$CHROOT_DIR/dev/null" ]; then mknod "$CHROOT_DIR/dev/null" c 1 3; fi
        if [ ! -c "$CHROOT_DIR/dev/random" ]; then mknod "$CHROOT_DIR/dev/random" c 1 8; fi
        chmod 666 "$CHROOT_DIR/dev/null" "$CHROOT_DIR/dev/random"

        echo "\$AddUnixListenSocket $CHROOT_DIR/dev/log" > /etc/rsyslog.d/bind-chroot.conf
        systemctl restart rsyslog

        # 首次配置时修改配置
        NAMED_CONF_OPTIONS_PATH="$CHROOT_DIR/etc/bind/named.conf.options"
        if ! grep -q "listen-on { any; };" "$NAMED_CONF_OPTIONS_PATH"; then
            echo "Configuring BIND options for the first time..."
#            sed -i '/^\s*listen-on\s/c\listen-on { any; };' "$NAMED_CONF_OPTIONS_PATH"
#            sed -i '/^\s*listen-on-v6\s/c\listen-on-v6 { none; };' "$NAMED_CONF_OPTIONS_PATH"
#            sed -i '/^\s*allow-query\s/c\allow-query { any; };' "$NAMED_CONF_OPTIONS_PATH"
#            sed -i '/^\s*recursion\s/c\recursion no;' "$NAMED_CONF_OPTIONS_PATH"
            cat > "$NAMED_CONF_OPTIONS_PATH" <<EOF
options {
    directory "/var/cache/bind";
    listen-on { any; };
    listen-on-v6 { none; };
    allow-query { any; };
    recursion no;
    pid-file "/var/run/named/named.pid";

    dnssec-validation auto;
    auth-nxdomain no;    # conform to RFC1035
};
EOF
        fi

        # 确保权限
        chown -R named:named "$CHROOT_DIR"

        # 处理 AppArmor
        if [ -d /etc/apparmor.d/ ]; then
            if [ ! -L /etc/apparmor.d/disable/usr.sbin.named ]; then
                echo "Disabling AppArmor for named to ensure chroot works correctly."
                ln -sf /etc/apparmor.d/usr.sbin.named /etc/apparmor.d/disable/
                apparmor_parser -R /etc/apparmor.d/usr.sbin.named
            fi
        fi

        systemctl disable pdns >/dev/null 2>&1
        systemctl stop pdns >/dev/null 2>&1

        systemctl daemon-reload
        systemctl restart bind9
        systemctl enable bind9
        echo "bind" > /www/server/panel/class_v2/ssl_dnsV2/aadns.pl
        echo "BIND9 with chroot installed and configured for Debian/Ubuntu."
        echo "Installed Success!"
    else
        echo "Error: Neither yum nor apt-get found. Cannot install BIND."
        exit 1
    fi
}

Install_aaDns()
{
    Install_Bind
}

Uninstall_aaDns()
{
    if command -v yum >/dev/null 2>&1; then
        SERVICE_NAME="named"
        if systemctl list-unit-files | grep -q "named-chroot.service"; then
            SERVICE_NAME="named-chroot"
        fi
        systemctl stop "$SERVICE_NAME"
        systemctl disable "$SERVICE_NAME"
        echo "BIND uninstalled from CentOS/RHEL."
    elif command -v apt-get >/dev/null 2>&1; then
        systemctl stop bind9
        systemctl disable bind9
        echo "BIND9 uninstalled from Debian/Ubuntu."
    else
        echo "Error: Neither yum nor apt-get found. Cannot uninstall BIND."
        exit 1
    fi
}

if [ "${1}" == "install" ];then
	Install_aaDns
fi
#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
public_file=/www/server/panel/install/public.sh

if [ ! -f $public_file ];then
	wget -O $public_file https://node.aapanel.com/install/public.sh -T 30;
fi

. $public_file
download_Url=$NODE_URL


check_and_disable_resolved()
{
  if systemctl is-active --quiet systemd-resolved; then
    echo "Found active systemd-resolved. Stopping and disabling it..."
    systemctl stop systemd-resolved
    systemctl disable systemd-resolved
    echo "systemd-resolved has been stopped and disabled."
  elif systemctl list-units --type=service --all | grep -q 'systemd-resolved.service'; then
    echo "Found inactive systemd-resolved. Disabling it..."
    systemctl disable systemd-resolved
    echo "systemd-resolved has been disabled."
  else
    echo "systemd-resolved service not found, no action needed."
  fi

  # 删软链
  if [ -L /etc/resolv.conf ]; then
        echo "Removing symlink /etc/resolv.conf"
        rm -f /etc/resolv.conf
        echo "Set namerser 8.8.8.8 to /etc/resolv.conf"
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
  fi
  # 确保上游dns
  if ! grep -q "nameserver 8.8.8.8" /etc/resolv.conf 2>/dev/null; then
      echo "Adding 8.8.8.8 to /etc/resolv.conf"
      echo "nameserver 8.8.8.8" >> /etc/resolv.conf
  fi
}

Install_Powerdns_Redhat()
{
  yum install pdns -y
  groupadd named
  useradd -g named -s /sbin/nologin named
  mv /etc/pdns/pdns.conf /etc/pdns/pdns.conf_bt
  wget -O /etc/pdns/pdns.conf $download_Url/install/plugin/dns_manager/pdns.conf -T 30
  chmod 644 /etc/pdns/pdns.conf
  mkdir -p /var/named/chroot/etc
  mkdir -p /var/named/chroot/var/named
  chmod  755 /var/named
  chmod  755 /var/named/chroot
  chmod  755 /var/named/chroot/etc
  chmod  755 /var/named/chroot/var
  chmod  755 /var/named/chroot/var/named
  chmod -R 644 /var/named/chroot/etc/*
  chmod -R 644 /var/named/chroot/var/named/*
  if [ ! -f "/var/named/chroot/etc/named.rfc1912.zones" ];then
    touch /var/named/chroot/etc/named.rfc1912.zones
  fi
  bind_conf=$(grep 'file "/var/' /var/named/chroot/etc/named.rfc1912.zones)
  if [ "$bind_conf" == "" ];then
    sed -i 's/file\s*\"/file \"\/var\/named\/chroot\/var\/named\//g' /var/named/chroot/etc/named.rfc1912.zones
  fi
  check_and_disable_resolved
	systemctl stop named-chroot
	systemctl disable named-chroot
  systemctl enable pdns
  systemctl restart pdns

  echo "Configured for Rehat/Centos."

}

Install_Powerdns_Ubuntu()
{
  curl https://repo.powerdns.com/FD380FBB-pub.asc | sudo apt-key add -
  apt-get update -y
  apt-get install pdns-server -y
  groupadd named
  useradd -g named -s /sbin/nologin named
  mv /etc/powerdns/pdns.conf /etc/powerdns/pdns.conf_bt
  wget -O /etc/powerdns/pdns.conf $download_Url/install/plugin/dns_manager/pdns.conf -T 30
  chmod 644 /etc/powerdns/pdns.conf
  mkdir -p /var/named/chroot/etc
  mkdir -p /var/named/chroot/var/named
  if [ ! -f "/var/named/chroot/etc/named.rfc1912.zones" ];then
    touch /var/named/chroot/etc/named.rfc1912.zones
  fi
  check_and_disable_resolved
  systemctl enable pdns
  systemctl restart pdns

  echo "Configured for Debian/Ubuntu."
}

Install_Powerdns()
{
  if [ -f '/usr/bin/yum' ];then
    Install_Powerdns_Redhat
  else
    Install_Powerdns_Ubuntu
  fi

  echo -n "pdns" > /www/server/panel/class_v2/ssl_dnsV2/aadns.pl
}

Install_DnsManager()
{
	echo "Installing..."
	Install_Powerdns
	/usr/bin/btpip install dnspython
	grep "English" /www/server/panel/config/config.json
	sleep 3
	echo "aaPanelDns Service Success!"
}

update_DnsManager()
{
  if [ ! -f "/usr/sbin/pdns_server" ];then
	echo "Installing ..."
  Install_Powerdns
  fi
	grep "English" /www/server/panel/config/config.json
	echo "The installation is complete"
}

Uninstall_DnsManager()
{
  echo "Uninstalling..."
  clean=${1}
  if [ "$clean" == 1 ];then
    echo "Cleaning up aaPanelDns config data..."
    rm -f /var/named/chroot/etc/named.rfc1912.zones_bak
    mv /var/named/chroot/etc/named.rfc1912.zones /var/named/chroot/etc/named.rfc1912.zones_bak
    echo "Remove config: named.rfc1912.zones"
    cp /var/named/chroot/var/named/*_aadef /var/named/chroot/var/named_bak/
    cp /var/named/chroot/var/named/*zone /var/named/chroot/var/named_bak/
    echo "Remove zone config files"
    rm -rf /var/named/chroot/var/named
  else
    echo "Backing up aaPanelDns config data..."
    cp /var/named/chroot/etc/named.rfc1912.zones /var/named/chroot/etc/named.rfc1912.zones_aabak
    echo "Backup config: named.rfc1912.zones"
    mkdir -p /var/named/chroot/var/named_bak/
    echo "Backup zone config files"
    cp /var/named/chroot/var/named/*_aadef /var/named/chroot/var/named_bak/
    cp /var/named/chroot/var/named/*zone /var/named/chroot/var/named_bak/
  fi

  rm -f /www/server/panel/class_v2/ssl_dnsV2/aadns.pl
  rm -f /www/server/panel/class_v2/ssl_dnsV2/aaDns_conf.json

	/usr/bin/systemctl stop named-chroot
	systemctl disable named-chroot
	systemctl stop pdns
	systemctl disable pdns
	sleep 3
	echo "aaPanelDns Service Success!"
}

if [ "${1}" == 'install' ];then
	Install_DnsManager
elif  [ "${1}" == 'update' ];then
	update_DnsManager
elif [ "${1}" == 'uninstall' ];then
	Uninstall_DnsManager ${2}
fi

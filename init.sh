#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8
is64bit=`getconf LONG_BIT`

if [ -f "/usr/bin/apt-get" ];then
	isDebian=`cat /etc/issue|grep Debian`
	if [ "$isDebian" != "" ];then
		wget -O install.sh http://www.aapanel.com/script/install-ubuntu_6.0_en.sh && bash install.sh
		exit;
	else
		wget -O install.sh http://www.aapanel.com/script/install-ubuntu_6.0_en.sh && sudo bash install.sh
		exit;
	fi
fi

if [ "$is64bit" != '64' ];then
	echo "====================================="
	echo "Sorry, 6.0 Does not support 32-bit systems, Use 64-bit system Please!";
	exit 0;
fi

py26=$(python -V 2>&1|grep '2.6.')
if [ "$py26" != "" ];then
	echo "====================================="
	echo "Sorry, 6.0 Does not support Centos6.x, Please install Centos7";
	exit 0;
fi

CN='http://125.88.182.172:5880'

Install_Check(){
	while [ "$yes" != 'yes' ] && [ "$yes" != 'n' ]
	do
		echo -e "----------------------------------------------------"
		echo -e "Web service is alreday installed,installing aaPanel may affect existing sites."
		echo -e "----------------------------------------------------"
		read -p "Enter yes to force installation (yes/n): " yes;
	done
	if [ "$yes" == 'n' ];then
		exit;
	fi
}

Web_Service_Check(){
	if [ -f "/etc/init.d/nginx" ]; then
        nginxV=$(cat /etc/init.d/nginx|grep /www/server/nginx)
        if [ "${nginxV}" = "" ];then
        	Install_Check
        fi
    fi

    if [ -f "/etc/init.d/httpd" ]; then
        httpdV=$(cat /etc/init.d/httpd|grep /www/server/apache)
        if [ "${httpdV}" = "" ];then
        	Install_Check
        fi
    fi

    if [ -f "/etc/init.d/mysqld" ]; then
        mysqlV=$(cat /etc/init.d/mysqld|grep /www/server/mysql)
        if [ "${mysqlV}" = "" ];then
        	Install_Check
        fi
    fi
}

Web_Service_Check

echo "
+----------------------------------------------------------------------
| aaPanel 6.0 FOR CentOS
+----------------------------------------------------------------------
| Copyright © 2015-2099 aaPanel(http://www.aapanel.com) All rights reserved.
+----------------------------------------------------------------------
| The WebPanel URL will be http://SERVER_IP:8888 when installed.
+----------------------------------------------------------------------
"
get_node_url(){
	nodes=(http://125.88.182.172:5880 http://183.235.223.101:3389 http://103.224.251.67 http://128.1.164.196);
	i=1;
	if [ ! -f /bin/curl ];then
		if [ -f /usr/local/curl/bin/curl ];then
			ln -sf /usr/local/curl/bin/curl /bin/curl
		else
			yum install curl -y
		fi
	fi
	for node in ${nodes[@]};
	do
		start=`date +%s.%N`
		result=`curl -sS --connect-timeout 3 -m 60 $node/check.txt`
		if [ $result = 'True' ];then
			end=`date +%s.%N`
			start_s=`echo $start | cut -d '.' -f 1`
			start_ns=`echo $start | cut -d '.' -f 2`
			end_s=`echo $end | cut -d '.' -f 1`
			end_ns=`echo $end | cut -d '.' -f 2`
			time_micro=$(( (10#$end_s-10#$start_s)*1000000 + (10#$end_ns/1000 - 10#$start_ns/1000) ))
			time_ms=$(($time_micro/1000))
			values[$i]=$time_ms;
			urls[$time_ms]=$node
			i=$(($i+1))
		fi
	done
	j=5000
	for n in ${values[@]};
	do
		if [ $j -gt $n ];then
			j=$n
		fi
	done
	if [ $j = 5000 ];then
		NODE_URL='http://download.bt.cn';
	else
		NODE_URL=${urls[$j]}
	fi

}
echo '---------------------------------------------';
echo "Selected download node...";
get_node_url
download_Url=$NODE_URL
echo "Download node: $download_Url";
echo '---------------------------------------------';
setup_path=/www
port='8888'
if [ -f $setup_path/server/panel/data/port.pl ];then
	port=`cat $setup_path/server/panel/data/port.pl`
fi

while [ "$go" != 'y' ] && [ "$go" != 'n' ]
do
	read -p "Do you want to install aaPanel to the $setup_path directory now?(y/n): " go;
done

if [ "$go" == 'n' ];then
	exit;
fi

path=/etc/yum.conf
isExc=`cat $path|grep httpd`
if [ "$isExc" = "" ];then
    echo "exclude=httpd nginx php mysql mairadb python-psutil python2-psutil" >> $path
fi

#自动挂载Swap
autoSwap()
{
	swap=`free |grep Swap|awk '{print $2}'`
	if [ $swap -gt 1 ];then
        echo "Swap total sizse: $swap";
		return;
	fi
	if [ ! -d /www ];then
		mkdir /www
	fi
	swapFile='/www/swap'
	dd if=/dev/zero of=$swapFile bs=1M count=1025
	mkswap -f $swapFile
    swapon $swapFile
    echo "$swapFile    swap    swap    defaults    0 0" >> /etc/fstab
	swap=`free |grep Swap|awk '{print $2}'`
	if [ $swap -gt 1 ];then
        echo "Swap total sizse: $swap";
		return;
	fi

	sed -i "/\/www\/swap/d" /etc/fstab
	rm -f $swapFile
}
autoSwap

#判断kernel-headers组件是否安装
rpm -qa | grep kernel-headers > kernel-headers.pl
kernelStatus=`cat kernel-headers.pl`
#判断华为云
huaweiLogin=`cat /etc/motd |grep 4000-955-988`
huaweiSys=`cat /etc/redhat-release | grep ' 7.'`
if [ "$kernelStatus" = "" ]; then
	if [ "$huaweiLogin" != "" ] && [ "$huaweiSys" != "" ]; then
		wget $download_Url/src/kernel-headers-3.10.0-514.el7.x86_64.rpm
		rpm -ivh kernel-headers-3.10.0-514.el7.x86_64.rpm
		rm -f kernel-headers-3.10.0-514.el7.x86_64.rpm
	else
		yum install kernel-headers -y
	fi
fi
rm -f kernel-headers.pl

#try sync time from bt.cn
echo 'Synchronizing system time...'
v1=$(curl http://www.bt.cn/api/index/get_time)
date -s "$(date -d @$v1 +"%Y-%m-%d %H:%M:%S")"

yum install ntp chrony -y
systemctl restart chrony
timedatectl set-ntp 1
#rm -rf /etc/localtime
#ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

#echo 'Synchronizing system time...'
#ntpdate 0.asia.pool.ntp.org
startTime=`date +%s`
setenforce 0
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
for pace in python-devel python-imaging zip unzip openssl openssl-devel gcc libxml2 libxml2-devel libxslt* zlib zlib-devel libjpeg-devel libpng-devel libwebp libwebp-devel freetype freetype-devel lsof pcre pcre-devel vixie-cron crontabs icu libicu-devel c-ares;
do
	yum -y install ${pace};
done

if [ -f "/usr/bin/dnf" ]; then
	dnf install -y redhat-rpm-config
fi
yum install python-devel -y

py26=$(python -V 2>&1|grep '2.6.')
if [ "$py26" != "" ];then
	if [ ! -f /etc/yum.repos.d/epel.repo ];then
		wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo
	fi
    if [ ! -f /usr/bin/python3 ];then
		yum install python34 python34-devel -y
		if [ ! -f /usr/bin/python3 ];then
			echo "python3.4 install error!"
			exit 0;
		fi
		isSed=$(cat /usr/bin/yum|grep /usr/bin/python2.6)
		if [ "$isSed" == "" ];then
			sed -i "s#/usr/bin/python#/usr/bin/python2.6#" /usr/bin/yum
		fi
		#rm -f /usr/bin/python2
		mv -f /usr/bin/python /usr/bin/python2_backup
		ln -sf /usr/bin/python3 /usr/bin/python
	fi
	if [ ! -f /usr/bin/pip3 ];then
		wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py
		python3 get-pip.py
		mv -f /usr/bin/pip /usr/bin/pip_backup
		ln -sf /usr/bin/pip3.4 /usr/bin/pip
	fi
fi

tmp=`python -V 2>&1|awk '{print $2}'`
pVersion=${tmp:0:3}

Install_setuptools()
{
	if [ ! -f "/usr/bin/easy_install" ];then
		wget -O setuptools-33.1.1.zip $download_Url/install/src/setuptools-33.1.1.zip -T 10
		unzip setuptools-33.1.1.zip
		rm -f setuptools-33.1.1.zip
		cd setuptools-33.1.1
		python setup.py install
		cd ..
		rm -rf setuptools-33.1.1
	fi

	if [ ! -f "/usr/bin/easy_install" ];then
		echo '=================================================';
		echo -e "\033[31msetuptools installation failed. \033[0m";
		exit;
	fi
}

Install_pip()
{
	ispip=`pip -V |grep from`
	if [ "$ispip" == "" ];then
		if [ ! -f "/usr/bin/easy_install" ];then
			Install_setuptools
		fi
		wget -O pip-9.0.1.tar.gz $download_Url/install/src/pip-9.0.1.tar.gz -T 10
		tar xvf pip-9.0.1.tar.gz
		rm -f pip-9.0.1.tar.gz
		cd pip-9.0.1
		python setup.py install
		cd ..
		rm -rf pip-9.0.1
	fi
	ispip=`pip -V |grep from`
	if [ "$ispip" = "" ];then
		echo '=================================================';
		echo -e "\033[31m Python-pip installation failed. \033[0m";
		exit;
	fi

	pip install -U pip
}

Install_Pillow()
{
	isSetup=`python -m PIL 2>&1|grep package`
	if [ "$isSetup" = "" ];then
		isFedora = `cat /etc/redhat-release |grep Fedora`
		if [ "$isFedora" != "" ];then
			pip install Pillow
			return;
		fi
		wget -O Pillow-3.2.0.zip $download_Url/install/src/Pillow-3.2.0.zip -T 10
		unzip Pillow-3.2.0.zip
		rm -f Pillow-3.2.0.zip
		cd Pillow-3.2.0
		python setup.py install
		cd ..
		rm -rf Pillow-3.2.0
	fi

	isSetup=`python -m PIL 2>&1|grep package`
	if [ "$isSetup" = "" ];then
		echo '=================================================';
		echo -e "\033[31mPillow installation failed. \033[0m";
		exit;
	fi
}

Install_psutil()
{
	isSetup=`python -m psutil 2>&1|grep package`
	if [ "$isSetup" = "" ];then
		wget -O psutil-5.2.2.tar.gz $download_Url/install/src/psutil-5.2.2.tar.gz -T 10
		tar xvf psutil-5.2.2.tar.gz
		rm -f psutil-5.2.2.tar.gz
		cd psutil-5.2.2
		python setup.py install
		cd ..
		rm -rf psutil-5.2.2
	fi
	isSetup=`python -m psutil 2>&1|grep package`
	if [ "$isSetup" = "" ];then
		echo '=================================================';
		echo -e "\033[31mpsutil installation failed. \033[0m";
		exit;
	fi
}

Install_mysqldb()
{
	isSetup=`python -m MySQLdb 2>&1|grep package`
	if [ "$isSetup" = "" ];then
		wget -O MySQL-python-1.2.5.zip $download_Url/install/src/MySQL-python-1.2.5.zip -T 10
		unzip MySQL-python-1.2.5.zip
		rm -f MySQL-python-1.2.5.zip
		cd MySQL-python-1.2.5
		python setup.py install
		cd ..
		rm -rf MySQL-python-1.2.5
	fi
}

Install_chardet()
{
	isSetup=`python -m chardet 2>&1|grep package`
	if [ "$isSetup" = "" ];then
		wget -O chardet-2.3.0.tar.gz $download_Url/install/src/chardet-2.3.0.tar.gz -T 10
		tar xvf chardet-2.3.0.tar.gz
		rm -f chardet-2.3.0.tar.gz
		cd chardet-2.3.0
		python setup.py install
		cd ..
		rm -rf chardet-2.3.0
	fi

	isSetup=`python -m chardet 2>&1|grep package`
	if [ "$isSetup" = "" ];then
		echo '=================================================';
		echo -e "\033[31mchardet installation failed. \033[0m";
		exit;
	fi
}


Install_setuptools
Install_pip

if [ "${download_Url}" = "$CN" ]; then
	if [ ! -d "/root/.pip" ];then
		mkdir ~/.pip
	fi
    cat > ~/.pip/pip.conf <<EOF
[global]
index-url = https://pypi.doubanio.com/simple/

[install]
trusted-host=pypi.doubanio.com
EOF
fi

isPsutil=`python -m psutil 2>&1|grep package`
if [ "$isPsutil" != "" ];then
	psutil_version=`python -c 'import psutil;print psutil.__version__;' |grep '5.'`
	if [ "$psutil_version" = '' ];then
		pip uninstall psutil -y
	fi
fi
yum install libffi-devel -y
pip install --upgrade setuptools
pip install -U pip
pip install six --upgrade --ignore-installed six
pip install itsdangerous==0.24
pip install paramiko==2.0.2
pip install flask-socketio==3.0.2
pip install python-socketio==2.1.2
pip install Werkzeug==0.15.1
for p_name in psutil chardet virtualenv Flask Flask-Session Flask-SocketIO flask-sqlalchemy Pillow gunicorn gevent-websocket requests;
do
	pip install ${p_name}
done

is_gevent=$(pip list|grep gevent)

if [ "$is_gevent" = "" ];then
	if [ -f /usr/bin/yum ];then
		yum install python-gevent -y
	else
		apt install python-gevent -y
	fi
fi

pip install psutil chardet virtualenv Flask Flask-Session Flask-SocketIO flask-sqlalchemy Pillow gunicorn gevent-websocket paramiko
Install_Pillow
Install_psutil

pip install gunicorn

if [  -f /www/server/mysql/bin/mysql ]; then
	pip install mysql-python
	Install_mysqldb
fi
Install_chardet

mkdir -p $setup_path/server/panel/logs
mkdir -p $setup_path/server/panel/vhost/apache
mkdir -p $setup_path/server/panel/vhost/nginx
mkdir -p $setup_path/server/panel/vhost/rewrite


if [ -f '/etc/init.d/bt' ];then
	/etc/init.d/bt stop
fi

mkdir -p /www/server
mkdir -p /www/wwwroot
mkdir -p /www/wwwlogs
mkdir -p /www/backup/database
mkdir -p /www/backup/site

if [ ! -f "/usr/bin/unzip" ];then
	#rm -f /etc/yum.repos.d/epel.repo
	yum install unzip -y
fi
wget -O panel.zip $download_Url/install/src/panel6_en.zip -T 10
wget -O /etc/init.d/bt $download_Url/install/src/bt6_en.init -T 10
if [ -f "$setup_path/server/panel/data/default.db" ];then
	if [ -d "/$setup_path/server/panel/old_data" ];then
		rm -rf $setup_path/server/panel/old_data
	fi
	mkdir -p $setup_path/server/panel/old_data
	mv -f $setup_path/server/panel/data/default.db $setup_path/server/panel/old_data/default.db
	mv -f $setup_path/server/panel/data/system.db $setup_path/server/panel/old_data/system.db
	mv -f $setup_path/server/panel/data/port.pl $setup_path/server/panel/old_data/port.pl
	mv -f $setup_path/server/panel/data/admin_path.pl $setup_path/server/panel/old_data/admin_path.pl
fi

unzip -o panel.zip -d $setup_path/server/ > /dev/null

if [ -d "$setup_path/server/panel/old_data" ];then
	mv -f $setup_path/server/panel/old_data/default.db $setup_path/server/panel/data/default.db
	mv -f $setup_path/server/panel/old_data/system.db $setup_path/server/panel/data/system.db
	mv -f $setup_path/server/panel/old_data/port.pl $setup_path/server/panel/data/port.pl
	mv -f $setup_path/server/panel/old_data/admin_path.pl $setup_path/server/panel/data/admin_path.pl
	if [ -d "/$setup_path/server/panel/old_data" ];then
		rm -rf $setup_path/server/panel/old_data
	fi
fi

rm -f panel.zip

if [ ! -f $setup_path/server/panel/tools.py ];then
	echo -e "\033[31mERROR: Failed to download, please try again!\033[0m";
	echo '============================================'
	exit;
fi

rm -f $setup_path/server/panel/class/*.pyc
rm -f $setup_path/server/panel/*.pyc



chmod +x /etc/init.d/bt
chkconfig --add bt
chkconfig --level 2345 bt on
chmod -R 600 $setup_path/server/panel
chmod -R +x $setup_path/server/panel/script
ln -sf /etc/init.d/bt /usr/bin/bt
echo "$port" > $setup_path/server/panel/data/port.pl
/etc/init.d/bt start

password=`cat /dev/urandom | head -n 16 | md5sum | head -c 8`
sleep 1
admin_auth='/www/server/panel/data/admin_path.pl'
if [ ! -f $admin_auth ];then
	auth_path=`cat /dev/urandom | head -n 16 | md5sum | head -c 8`
	echo "/$auth_path" > $admin_auth
fi
auth_path=`cat $admin_auth`
cd $setup_path/server/panel/
python -m py_compile tools.py
python tools.py username
username=`python tools.py panel $password`
cd ~
echo "$password" > $setup_path/server/panel/default.pl
chmod 600 $setup_path/server/panel/default.pl
/etc/init.d/bt restart
sleep 3
isStart=`ps aux |grep 'gunicorn'|grep -v grep|awk '{print $2}'`
if [ "$isStart" == '' ];then
	echo -e "\033[31mERROR: The aaPanel service startup failed.\033[0m";
	echo '============================================'
	exit;
fi

if [ -f "/etc/init.d/iptables" ];then
	sshPort=`cat /etc/ssh/sshd_config | grep 'Port ' | grep -oE [0-9] | tr -d '\n'`
	if [ "${sshPort}" != "22" ]; then
		iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport $sshPort -j ACCEPT
	fi
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 20 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 21 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport $port -j ACCEPT
	iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 39000:40000 -j ACCEPT
	#iptables -I INPUT -p tcp -m state --state NEW -m udp --dport 39000:40000 -j ACCEPT
	iptables -A INPUT -p icmp --icmp-type any -j ACCEPT
	iptables -A INPUT -s localhost -d localhost -j ACCEPT
	iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
	iptables -P INPUT DROP
	service iptables save
	sed -i "s#IPTABLES_MODULES=\"\"#IPTABLES_MODULES=\"ip_conntrack_netbios_ns ip_conntrack_ftp ip_nat_ftp\"#" /etc/sysconfig/iptables-config

	iptables_status=`service iptables status | grep 'not running'`
	if [ "${iptables_status}" == '' ];then
		service iptables restart
	fi
fi

if [ "${isVersion}" == '' ];then
	if [ ! -f "/etc/init.d/iptables" ];then
		sshPort=`cat /etc/ssh/sshd_config | grep 'Port ' | grep -oE [0-9] | tr -d '\n'`
		yum install firewalld -y
		systemctl enable firewalld
		systemctl start firewalld
		firewall-cmd --set-default-zone=public > /dev/null 2>&1
		if [ "${sshPort}" != "22" ]; then
			firewall-cmd --permanent --zone=public --add-port=$sshPort/tcp > /dev/null 2>&1
		fi
		firewall-cmd --permanent --zone=public --add-port=20/tcp > /dev/null 2>&1
		firewall-cmd --permanent --zone=public --add-port=21/tcp > /dev/null 2>&1
		firewall-cmd --permanent --zone=public --add-port=22/tcp > /dev/null 2>&1
		firewall-cmd --permanent --zone=public --add-port=80/tcp > /dev/null 2>&1
		firewall-cmd --permanent --zone=public --add-port=$port/tcp > /dev/null 2>&1
		firewall-cmd --permanent --zone=public --add-port=39000-40000/tcp > /dev/null 2>&1
		#firewall-cmd --permanent --zone=public --add-port=39000-40000/udp > /dev/null 2>&1
		firewall-cmd --reload
	fi
fi

pip install psutil chardet psutil virtualenv cryptography==2.1 > /dev/null 2>&1

if [ ! -d '/etc/letsencrypt' ];then
	yum install epel-release -y

	if [ "${country}" = "CN" ]; then
		isC7=`cat /etc/redhat-release |grep ' 7.'`
		if [ "${isC7}" == "" ];then
			wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-6.repo
		else
			wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo
		fi
	fi
	mkdir -p /var/spool/cron
	if [ ! -f '/var/spool/cron/root' ];then
		echo '' > /var/spool/cron/root
		chmod 600 /var/spool/cron/root
	fi
fi

wget -O acme_install.sh $download_Url/install/acme_install.sh
nohup bash acme_install.sh &> /dev/null &
sleep 1
rm -f acme_install.sh

address=""
address=`curl -sS --connect-timeout 10 -m 60 https://www.bt.cn/Api/getIpAddress`
if [ "$address" == '0.0.0.0' ] || [ "$address" == '' ];then
	isHosts=`cat /etc/hosts|grep 'www.bt.cn'`
	if [ "$isHosts" == '' ];then
		echo "" >> /etc/hosts
		echo "125.88.182.170 www.bt.cn" >> /etc/hosts
		address=`curl -sS --connect-timeout 10 -m 60 https://www.bt.cn/Api/getIpAddress`
		if [ "$address" == '' ];then
			sed -i "/bt.cn/d" /etc/hosts
		fi
	fi
fi

ipCheck=`python -c "import re; print(re.match('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$','$address'))"`
if [ "$ipCheck" == "None" ];then
	address="SERVER_IP"
fi

if [ "$address" != "SERVER_IP" ];then
	echo "$address" > $setup_path/server/panel/data/iplist.txt
fi

curl -sS --connect-timeout 10 -m 60 https://www.bt.cn/Api/SetupCount?type=Linux\&o=EN > /dev/null 2>&1
curl -sS --connect-timeout 10 -m 60 https://www.aapanel.com/Api/SetupCount?type=Linux > /dev/null 2>&1
echo /www > /var/bt_setupPath.conf
/etc/init.d/bt start

echo -e "=================================================================="
echo -e "\033[32mCongratulations! Installed successfully!\033[0m"
echo -e "=================================================================="
echo  "aaPanel: http://$address:$port$auth_path"
echo -e "username: $username"
echo -e "password: $password"
echo -e "\033[33mWarning:\033[0m"
echo -e "\033[33mIf you cannot access the panel, \033[0m"
echo -e "\033[33mrelease the following port (8888|888|80|443|20|21) in the security group\033[0m"
echo -e "=================================================================="

endTime=`date +%s`
((outTime=($endTime-$startTime)/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"
rm -f install.sh
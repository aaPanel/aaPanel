#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
install_tmp='/tmp/bt_install.pl'
download_Url=http://download.bt.cn
Install_Ftp()
{	
	echo 'Installing script files...' > $install_tmp
	wget -O /www/server/panel/script/backup_ftp.py $download_Url/install/lib/script/backup_ftp.py -T 5
	
	echo 'The installation is complete' > $install_tmp
}

Uninstall_Ftp()
{
	rm -f /www/server/panel/script/backup_ftp.py
	echo 'Uninstall complete' > $install_tmp
}


action=$1
if [ "${1}" == 'install' ];then
	Install_Ftp
else
	Uninstall_Ftp
fi

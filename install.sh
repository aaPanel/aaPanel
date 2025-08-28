#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8

if [ $(whoami) != "root" ]; then
    # echo "Please use the [root] user to execute the aapanel installation script!"
    echo -e "Non-root install, please try the following solutions: \n   1.Please switch to [root] user install \n   2.Try executing the following install commands: \n     sudo bash $0 $@"
    exit 1
fi

is64bit=$(getconf LONG_BIT)
if [ "${is64bit}" != '64' ]; then
    Red_Error "Sorry, aaPanel does not support 32-bit systems"
fi

HOSTNAME_CHECK=$(cat /etc/hostname)
if [ -z "${HOSTNAME_CHECK}" ];then
    echo "hostname is empty. Already set as aaPanel"
    echo "aaPanel" > /etc/hostname
    hostnamectl set-hostname aaPanel
fi

if [ -f "/etc/SUSE-brand" ];then
    openSUSE_check=$(cat /etc/SUSE-brand |grep openSUSE)
    if [ "${openSUSE_check}" ];then
        echo "Error: openSUSE not supported, Recommended that you use:"
        echo "Debian 11/12, Ubuntu 20/22/24, Rocky/Alma 8, Rocky/Alma/Centos 9"        
        exit 1
    fi
fi

cd ~
setup_path="/www"
python_bin=$setup_path/server/panel/pyenv/bin/python
cpu_cpunt=$(cat /proc/cpuinfo | grep ^processor | wc -l)
panelPort=$(expr $RANDOM % 55535 + 10000)
if [ "$1" ]; then
    IDC_CODE=$1
fi

Command_Exists() {
    command -v "$@" >/dev/null 2>&1
}

GetSysInfo() {
    if [ -s "/etc/redhat-release" ]; then
        SYS_VERSION=$(cat /etc/redhat-release)
    elif [ -s "/etc/issue" ]; then
        SYS_VERSION=$(cat /etc/issue)
    fi
    SYS_INFO=$(uname -a)
    SYS_BIT=$(getconf LONG_BIT)
    MEM_TOTAL=$(free -m | grep Mem | awk '{print $2}')
    CPU_INFO=$(getconf _NPROCESSORS_ONLN)

    echo -e ${SYS_VERSION}
    echo -e Bit:${SYS_BIT} Mem:${MEM_TOTAL}M Core:${CPU_INFO}
    echo -e ${SYS_INFO}
    echo -e "Please screenshot above error message and post forum forum.aapanel.com or send email: support@aapanel.com for help"
}


Replace_symbol(){
# 更换符号为__
    text="${text#"${text%%[![:space:]]*}"}"
    text=${text%% }
    text=${text// /__}
    text=${text//\（/__}
    text=${text//\）/__}
    text=${text//\"/__}
    text=${text//\“/__}
    text=${text//\”/__}
    text=${text//\(/__}
    text=${text//\)/__}
    text=${text//\!/__}
    text=${text//\！/__}
    text=${text//:/__}
    text=${text//：/__}
    text=${text//,/__}
    text=${text//，/__}
    text=${text//。/__}
    text=${text//\$/__}
    text=${text//\{/__}
    text=${text//\}/__}
    text=${text//\[/__}
    text=${text//\]/__}
    text=${text//./__}
    text=${text//-/__}
    text=${text//>/__}
    text=${text//=/__}
    text=${text//\//__}
    text=${text//\'/__}
    
}

Little_tail() {

    arch=$(uname -m)

    if [ -s "/etc/redhat-release" ];then
        SYS_VERSION=$(cat /etc/redhat-release)
    elif Command_Exists hostnamectl; then
        SYS_VERSION=$(hostnamectl | grep "Operating System" | awk -F":" '{print $2}')
    elif [ -s "/etc/issue" ]; then
        SYS_VERSION=$(cat /etc/issue | tr '\n' ' ')
    fi
    
    text="${SYS_VERSION}_${arch}"
    Replace_symbol
    # echo "$text"
    system="$text"

    curl -o /dev/null -fsSLk --connect-time 10 "https://www.aapanel.com/api/setupCount/setupPanelFailed?type=Linux&os=${system}&errmsg=${url_err_msg}" >/dev/null 2>&1

}

Red_Error() {
    echo '================================================='
    printf '\033[1;31;40m%b\033[0m\n' "$@"
    GetSysInfo

    if [[ "$@" == "" ]]; then
        url_err_msg="aaPanel_install_failed"
    else
        text="$@"
        Replace_symbol

        url_err_msg="${text}"
        #echo "url_err_msg：$url_err_msg"
    fi
    Little_tail

    exit 1
}

if [ -f "/etc/redhat-release" ]; then
    Centos6Check=$(cat /etc/redhat-release | grep ' 6.' | grep -iE 'centos|Red Hat')
    if [ "${Centos6Check}" ]; then
        Red_Error "Sorry, Centos6 does not support installing aaPanel"
    fi
    Centos7Check=$(cat /etc/redhat-release | grep ' 7.' | grep -iE 'centos|Red Hat')
    Centos8Check=$(cat /etc/redhat-release | grep ' 8.' | grep -iE 'centos|Red Hat')
    if [ "${Centos7Check}" ] || [ "${Centos8Check}" ];then
        echo "Centos 7/8 provider no longer maintained, Recommended that you use:"
        echo "Debian 11/12, Ubuntu 20/22/24, Rocky/Alma 8, Rocky/Alma/Centos 9"
        echo "Press Ctrl+C to cancel or Wait 10 seconds before install"
        sleep 10
    fi
fi

if [ -f "/etc/issue" ]; then
    UbuntuCheck=$(cat /etc/issue | grep Ubuntu | awk '{print $2}' | cut -f 1 -d '.')
    if [[ ! -z "${UbuntuCheck}" ]] && [[ "${UbuntuCheck}" =~ ^[0-9]+$ ]] && [[ "${UbuntuCheck}" -lt "18" ]]; then
        Red_Error "Ubuntu ${UbuntuCheck} is not supported to the aaPanel, it is recommended to replace the Ubuntu 20/22/24 to install"
    fi

    DebianCheck=$(cat /etc/issue | grep Debian | awk '{print $3}' | cut -f 1 -d '.')
    if [[ ! -z "${DebianCheck}" ]] && [[ "${DebianCheck}" =~ ^[0-9]+$ ]]  && [[ "${DebianCheck}" -lt "10" ]]; then
        Red_Error "Debian ${DebianCheck} is not supported to the aaPanel, it is recommended to replace the Debian 11/12 to install"
    fi
fi

Check_Disk_Space() {
    # Get the available space of the partition where the /www directory is located (in kb)
    if [ -d "/www" ]; then
        available_kb=$(df -k /www | awk 'NR==2 {print $4}')
    else
        available_kb=$(df -k / | awk 'NR==2 {print $4}')
    fi
    
    # 1GB = 1024MB = 1024*1024KB
    available_gb=$((available_kb / 1024 / 1024))
    echo "Available disk space on the install partition: "$available_gb" G"

    # Determine if available space is less than 1 gb
    if [ "$available_gb" -lt 1 ]; then
        echo -e "\033[31m The available space is less than 1G.\033[0m"
        echo -e "\033[31m It is recommended to clean or upgrade the server space before upgrading.\033[0m"
        Red_Error "Error: The available space is less than 1G"
    fi

}

Lock_Clear() {
    if [ -f "/etc/bt_crack.pl" ]; then
        chattr -R -ia /www
        chattr -ia /etc/init.d/bt
        \cp -rpa /www/backup/panel/vhost/* /www/server/panel/vhost/
        mv /www/server/panel/BTPanel/__init__.bak /www/server/panel/BTPanel/__init__.py
        rm -f /etc/bt_crack.pl
    fi
}
Install_Check() {
    if [ "${INSTALL_FORCE}" ]; then
        return
    fi
    echo -e "----------------------------------------------------"
    echo -e "Web service is already installed,installing aaPanel may affect existing sites."
    echo -e "----------------------------------------------------"
    echo -e "Enter [yes] to force installation"
    read -p "Enter yes to force installation: " yes
    if [ "$yes" != "yes" ]; then
        echo -e "------------"
        echo "Installation canceled"
        exit
    fi
    INSTALL_FORCE="true"
}
System_Check() {
    MYSQLD_CHECK=$(ps -ef | grep mysqld | grep -v grep | grep -v /www/server/mysql)
    PHP_CHECK=$(ps -ef | grep php-fpm | grep master | grep -v /www/server/php)
    NGINX_CHECK=$(ps -ef | grep nginx | grep master | grep -v /www/server/nginx)
    HTTPD_CHECK=$(ps -ef | grep -E 'httpd|apache' | grep -v /www/server/apache | grep -v grep)
    if [ "${PHP_CHECK}" ] || [ "${MYSQLD_CHECK}" ] || [ "${NGINX_CHECK}" ] || [ "${HTTPD_CHECK}" ]; then
        Install_Check
    fi
}
Set_Ssl() {
    SET_SSL=true

    if [ "${SSL_PL}" ];then
    	SET_SSL=""
    fi
}

Get_Pack_Manager() {
    if [ -f "/usr/bin/yum" ] && [ -d "/etc/yum.repos.d" ]; then
        PM="yum"
    elif [ -f "/usr/bin/apt-get" ] && [ -f "/usr/bin/dpkg" ]; then
        PM="apt-get"
    fi
}

Auto_Swap() {
    swap=$(free | grep Swap | awk '{print $2}')
    if [ "${swap}" -gt 1 ]; then
        echo "Swap total sizse: $swap"
        return
    fi
    if [ ! -d /www ]; then
        mkdir /www
    fi
    swapFile="/www/swap"
    dd if=/dev/zero of=$swapFile bs=1M count=1025
    mkswap -f $swapFile
    swapon $swapFile
    echo "$swapFile    swap    swap    defaults    0 0" >>/etc/fstab
    swap=$(free | grep Swap | awk '{print $2}')
    if [ $swap -gt 1 ]; then
        echo "Swap total sizse: $swap"
        return
    fi

    sed -i "/\/www\/swap/d" /etc/fstab
    rm -f $swapFile
}
Service_Add() {
    if Command_Exists systemctl ; then
        wget --no-check-certificate -O /usr/lib/systemd/system/btpanel.service ${download_Url}/init/systemd/btpanel.service -t 5 -T 20
        systemctl daemon-reload
        systemctl enable btpanel

    else
        if [ "${PM}" == "yum" ] || [ "${PM}" == "dnf" ]; then
            chkconfig --add bt
            chkconfig --level 2345 bt on
        elif [ "${PM}" == "apt-get" ]; then
            update-rc.d bt defaults
        fi    
    fi
}

Set_Centos7_Repo(){
    MIRROR_CHECK=$(cat /etc/yum.repos.d/CentOS-Base.repo |grep "[^#]mirror.centos.org")
    if [ "${MIRROR_CHECK}" ] && [ "${is64bit}" == "64" ];then
        echo "Centos7 official repository source has been discontinued , Replacement in progress."
        if [ -d "/etc/yumBak" ];then
            mv /etc/yumBak /etc/yumBak_$(date +%Y_%m_%d_%H_%M_%S)
        fi
        \cp -rpa /etc/yum.repos.d/ /etc/yumBak
        sed -i 's/mirrorlist=/#mirrorlist=/g' /etc/yum.repos.d/CentOS-*.repo
        sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.epel.cloud|g' /etc/yum.repos.d/CentOS-*.repo
    fi

    MIRROR_CHECK22=$(cat /etc/yum.repos.d/CentOS-Base.repo |grep "mirrorlist.centos.org"|grep -v '^#')
    if [ "${MIRROR_CHECK22}" ] && [ "${is64bit}" == "64" ];then
        echo "Centos7 official repository source has been discontinued , Replacement in progress."
        if [ -d "/etc/yumBak" ];then
            mv /etc/yumBak /etc/yumBak_$(date +%Y_%m_%d_%H_%M_%S)
        fi
        \cp -rpa /etc/yum.repos.d/ /etc/yumBak
        \cp -rpa /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo_bt_bak
cat > /etc/yum.repos.d/CentOS-Base.repo << EOF

# CentOS-Base.repo

[base]
name=CentOS-\$releasever - Base
#mirrorlist=http://mirrorlist.centos.org/?release=\$releasever&arch=\$basearch&repo=os&infra=\$infra
baseurl=http://vault.epel.cloud/centos/\$releasever/os/\$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

#released updates 
[updates]
name=CentOS-\$releasever - Updates
#mirrorlist=http://mirrorlist.centos.org/?release=\$releasever&arch=\$basearch&repo=updates&infra=\$infra
baseurl=http://vault.epel.cloud/centos/\$releasever/updates/\$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

#additional packages that may be useful
[extras]
name=CentOS-\$releasever - Extras
#mirrorlist=http://mirrorlist.centos.org/?release=\$releasever&arch=\$basearch&repo=extras&infra=\$infra
baseurl=http://vault.epel.cloud/centos/\$releasever/extras/\$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

#additional packages that extend functionality of existing packages
[centosplus]
name=CentOS-\$releasever - Plus
#mirrorlist=http://mirrorlist.centos.org/?release=\$releasever&arch=\$basearch&repo=centosplus&infra=\$infra
baseurl=http://vault.epel.cloud/centos/\$releasever/centosplus/\$basearch/
gpgcheck=1
enabled=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7

EOF

    fi

    ALI_CLOUD_CHECK=$(grep Alibaba /etc/motd)
    Tencent_Cloud=$(cat /etc/hostname |grep -E VM-[0-9]+-[0-9]+)
    if [ "${ALI_CLOUD_CHECK}" ] || [ "${Tencent_Cloud}" ];then
        return
    fi

    yum install unzip -y
    if [ "$?" != "0" ] ;then
        TAR_CHECK=$(which tar)
        if [ "$?" == "0" ] ;then
            if [ -d "/etc/yumBak" ];then
                mv /etc/yumBak /etc/yumBak_$(date +%Y_%m_%d_%H_%M_%S)
            fi
            \cp -rpa /etc/yum.repos.d/ /etc/yumBak
            if [ -z "${download_Url}" ];then
                download_Url="https://node.aapanel.com"
            fi
            curl -Ssk --connect-timeout 20 -m 60 -O ${download_Url}/src/el7repo.tar.gz
            if [ -f "/usr/bin/wget" ] && [ ! -s "el7repo.tar.gz" ];then
                wget --no-check-certificate -O el7repo.tar.gz ${download_Url}/src/el7repo.tar.gz -t 3 -T 20
            fi
            rm -f /etc/yum.repos.d/*.repo
            tar -xvzf el7repo.tar.gz -C /etc/yum.repos.d/
            rm -f el7repo.tar.gz
        fi
    fi

}

Set_Centos8_Repo(){
    HUAWEI_CHECK=$(cat /etc/motd |grep "Huawei Cloud")
    if [ "${HUAWEI_CHECK}" ] && [ "${is64bit}" == "64" ];then
        \cp -rpa /etc/yum.repos.d/ /etc/yumBak
        sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*.repo
        sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.epel.cloud|g' /etc/yum.repos.d/CentOS-*.repo
        rm -f /etc/yum.repos.d/epel.repo
        rm -f /etc/yum.repos.d/epel-*
    fi
    ALIYUN_CHECK=$(cat /etc/motd|grep "Alibaba Cloud ")
    if [  "${ALIYUN_CHECK}" ] && [ "${is64bit}" == "64" ] && [ ! -f "/etc/yum.repos.d/Centos-vault-8.5.2111.repo" ];then
        rename '.repo' '.repo.bak' /etc/yum.repos.d/*.repo
        wget https://mirrors.aliyun.com/repo/Centos-vault-8.5.2111.repo -O /etc/yum.repos.d/Centos-vault-8.5.2111.repo
        wget https://mirrors.aliyun.com/repo/epel-archive-8.repo -O /etc/yum.repos.d/epel-archive-8.repo
        sed -i 's/mirrors.cloud.aliyuncs.com/url_tmp/g'  /etc/yum.repos.d/Centos-vault-8.5.2111.repo &&  sed -i 's/mirrors.aliyun.com/mirrors.cloud.aliyuncs.com/g' /etc/yum.repos.d/Centos-vault-8.5.2111.repo && sed -i 's/url_tmp/mirrors.aliyun.com/g' /etc/yum.repos.d/Centos-vault-8.5.2111.repo
        sed -i 's/mirrors.aliyun.com/mirrors.cloud.aliyuncs.com/g' /etc/yum.repos.d/epel-archive-8.repo
    fi
    MIRROR_CHECK=$(cat /etc/yum.repos.d/CentOS-Linux-AppStream.repo |grep "[^#]mirror.centos.org")
    if [ "${MIRROR_CHECK}" ] && [ "${is64bit}" == "64" ];then
        \cp -rpa /etc/yum.repos.d/ /etc/yumBak
        sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*.repo
        sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.epel.cloud|g' /etc/yum.repos.d/CentOS-*.repo
    fi

    yum install unzip tar -y
    if [ "$?" != "0" ] ;then
        if [ -z "${download_Url}" ];then
            download_Url="https://node.aapanel.com"
        fi
        if [ ! -f "/usr/bin/tar" ] ;then
            curl -Ss --connect-timeout 20 -m 60 -O ${download_Url}/src/tar-1.30-5.el8.x86_64.rpm
            if [ -f "/usr/bin/wget" ] && [ ! -s "tar-1.30-5.el8.x86_64.rpm" ];then
                wget --no-check-certificate -O tar-1.30-5.el8.x86_64.rpm ${download_Url}/src/tar-1.30-5.el8.x86_64.rpm -t 3 -T 20
            fi
            # yum install tar-1.30-5.el8.x86_64.rpm -y
            rpm -ivh tar-1.30-5.el8.x86_64.rpm
            rm -f tar-1.30-5.el8.x86_64.rpm
        fi
        if [ -d "/etc/yumBak" ];then
            mv /etc/yumBak /etc/yumBak_$(date +%Y_%m_%d_%H_%M_%S)
        fi
        \cp -rpa /etc/yum.repos.d/ /etc/yumBak
        curl -Ss --connect-timeout 20 -m 60 -O ${download_Url}/src/el8repo.tar.gz
        if [ -f "/usr/bin/wget" ] && [ ! -s "el8repo.tar.gz" ];then
            wget --no-check-certificate -O el8repo.tar.gz ${download_Url}/src/el8repo.tar.gz -t 3 -T 20
        fi
        rm -f /etc/yum.repos.d/*.repo
        tar -xvzf el8repo.tar.gz -C /etc/yum.repos.d/
        rm -f el8repo.tar.gz
    fi

}

Bored_waiting(){
    w_time="$wait_time"
    msg="$wait_msg"
    progress="."
    for ((i=0; i<${w_time}; i++))
    do
        printf "$msg %-10s %d\r" "$progress" "$((i+1))"
        sleep 1

        if [ "$progress" == ".........." ]; then
            progress="."
        else
            progress+="."
        fi
    done
    printf "$msg %-10s %d\r" ".........." "$w_time"
    #echo ""
}

Check_apt_status(){

    MAX_RETRIES=30
    retries=0

    while [ $retries -lt $MAX_RETRIES ]; do
        output=$(ps aux |grep -E '(apt|apt-get)\s' 2>&1)
        check_output=$(echo "$output" | grep -v _apt | grep -E '(apt|apt-get)\s')
        
        #If check_output is empty, terminate the loop
        if [ -z "$check_output" ]; then
            break
        fi

        retries=$((retries + 1))

        echo "apt-get is in use, it will automatically exit after ${retries}/${MAX_RETRIES} times, try again after 10 seconds..."
        echo "$check_output"
        wait_msg="Please wait"
        wait_time="10"
        Bored_waiting
        
    done

    if [ $retries -ge $MAX_RETRIES ]; then
        Red_Error "ERROR: apt-get command exceeds the maximum wait times: ${MAX_RETRIES}." "Do not use the apt/apt-get command or install software during installation, please try to reinstall!"
    fi

}

get_node_url() {

    download_Url='https://node.aapanel.com'

    if [ ! -f /bin/curl ]; then
        if [ "${PM}" = "yum" ]; then
            yum install curl -y
        elif [ "${PM}" = "apt-get" ]; then
            apt-get install curl -y
        fi
    fi

    if [ -f "/www/node.pl" ];then
        download_Url=$(cat /www/node.pl)
        echo "Download node: $download_Url";
        echo '---------------------------------------------';
        return
    fi
    
    # echo '---------------------------------------------';
    # echo "Selected download node...";
    # nodes=(https://node.aapanel.com);

    # if [ "$1" ];then
    #     nodes=($(echo ${nodes[*]}|sed "s#${1}##"))
    # fi
    # tmp_file1=/dev/shm/net_test1.pl
    # tmp_file2=/dev/shm/net_test2.pl

    # [ -f "${tmp_file1}" ] && rm -f ${tmp_file1}

    # [ -f "${tmp_file2}" ] && rm -f ${tmp_file2}

    # touch $tmp_file1
    # touch $tmp_file2
    # for node in ${nodes[@]}; do
    #     NODE_CHECK=$(curl -k --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/net_test|xargs)
    #     RES=$(echo ${NODE_CHECK} | awk '{print $1}')
    #     NODE_STATUS=$(echo ${NODE_CHECK} | awk '{print $2}')
    #     TIME_TOTAL=$(echo ${NODE_CHECK} | awk '{print $3 * 1000 - 500 }' | cut -d '.' -f 1)
    #     if [ "${NODE_STATUS}" == "200" ]; then
    #         if [ $TIME_TOTAL -lt 100 ]; then
    #             if [ $RES -ge 1500 ]; then
    #                 echo "$RES $node" >>$tmp_file1
    #             fi
    #         else
    #             if [ $RES -ge 1500 ]; then
    #                 echo "$TIME_TOTAL $node" >>$tmp_file2
    #             fi
    #         fi

    #         i=$(($i + 1))
    #         if [ $TIME_TOTAL -lt 100 ]; then
    #             if [ $RES -ge 3000 ]; then
    #                 break
    #             fi
    #         fi

    #     fi
    # done

    # NODE_URL=$(cat $tmp_file1 | sort -r -g -t " " -k 1 | head -n 1 | awk '{print $2}')
    # if [ -z "$NODE_URL" ]; then
    #     NODE_URL=$(cat $tmp_file2 | sort -g -t " " -k 1 | head -n 1 | awk '{print $2}')
    #     if [ -z "$NODE_URL" ]; then
    #         NODE_URL='https://node.aapanel.com'
    #     fi
    # fi

    # rm -f $tmp_file1
    # rm -f $tmp_file2
    # download_Url=$NODE_URL
    # echo "Download node: $download_Url"
    # echo '---------------------------------------------'

}
Remove_Package() {
    local PackageNmae=$1
    if [ "${PM}" == "yum" ]; then
        isPackage=$(rpm -q ${PackageNmae} | grep "not installed")
        if [ -z "${isPackage}" ]; then
            yum remove ${PackageNmae} -y
        fi
    elif [ "${PM}" == "apt-get" ]; then
        isPackage=$(dpkg -l | grep ${PackageNmae})
        if [ "${PackageNmae}" ]; then
            apt-get remove ${PackageNmae} -y
        fi
    fi
}
Install_RPM_Pack() {
    yumPath=/etc/yum.conf
    Centos8Check=$(cat /etc/redhat-release | grep ' 8.' | grep -iE 'centos|Red Hat')
    CentOS_Stream_8=$(cat /etc/redhat-release | grep 'CentOS Stream release 8' | grep -iE 'centos|Red Hat')
    if [ "${Centos8Check}" ] || [ "${CentOS_Stream_8}" ];then
        Set_Centos8_Repo
    fi
    Centos7Check=$(cat /etc/redhat-release | grep ' 7.' | grep -iE 'centos|Red Hat')
    if [ "${Centos7Check}" ];then
        Set_Centos7_Repo
    fi

    isExc=$(cat $yumPath | grep httpd)
    if [ "$isExc" = "" ]; then
        echo "exclude=httpd nginx php mysql mairadb python-psutil python2-psutil" >>$yumPath
    fi

    if [ -f "/etc/redhat-release" ] && [ $(cat /etc/os-release|grep PLATFORM_ID|grep -oE "el8") ];then
        yum config-manager --set-enabled powertools
        yum config-manager --set-enabled PowerTools
    fi

    if [ -f "/etc/redhat-release" ] && [ $(cat /etc/os-release|grep PLATFORM_ID|grep -oE "el9|el10") ];then
        dnf config-manager --set-enabled crb -y
    fi

    #yumBaseUrl=$(cat /etc/yum.repos.d/CentOS-Base.repo|grep baseurl=http|cut -d '=' -f 2|cut -d '$' -f 1|head -n 1)
    #[ "${yumBaseUrl}" ] && checkYumRepo=$(curl --connect-timeout 5 --head -s -o /dev/null -w %{http_code} ${yumBaseUrl})
    #if [ "${checkYumRepo}" != "200" ];then
    #	curl -Ss --connect-timeout 3 -m 60 http://node.aapanel.com/install/yumRepo_select.sh|bash
    #fi

    #尝试同步时间(从bt.cn)
    # 	echo 'Synchronizing system time...'
    # 	getBtTime=$(curl -sS --connect-timeout 3 -m 60 http://www.bt.cn/api/index/get_time)
    # 	if [ "${getBtTime}" ];then
    #     		date -s "$(date -d @$getBtTime +"%Y-%m-%d %H:%M:%S")"
    # 	fi

    #if [ -z "${Centos8Check}" ]; then
    #	yum install ntp -y
    #	rm -rf /etc/localtime
    #	ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

    #尝试同步国际时间(从ntp服务器)
    #	ntpdate 0.asia.pool.ntp.org
    #	setenforce 0
    #fi
    setenforce 0
    startTime=$(date +%s)

    sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
    #yum remove -y python-requests python3-requests python-greenlet python3-greenlet
    yumPacks="libcurl-devel wget tar gcc make zip unzip openssl openssl-devel gcc libxml2 libxml2-devel libxslt* zlib zlib-devel libjpeg-devel libpng-devel libwebp libwebp-devel freetype freetype-devel lsof pcre pcre-devel vixie-cron crontabs icu libicu-devel c-ares libffi-devel bzip2-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel firewalld ipset libpq-devel ca-certificates sudo at mariadb rsyslog autoconf xfsprogs quota"
    yum install -y ${yumPacks}

    for yumPack in ${yumPacks}; do
        rpmPack=$(rpm -q ${yumPack})
        packCheck=$(echo ${rpmPack} | grep not)
        if [ "${packCheck}" ]; then
            yum install ${yumPack} -y
        fi
    done
    if [ -f "/usr/bin/dnf" ]; then
        dnf install -y redhat-rpm-config
    fi

    ALI_OS=$(cat /etc/redhat-release | grep "Alibaba Cloud Linux release 3")
    if [ -z "${ALI_OS}" ]; then
        yum install epel-release -y
    fi
}
Install_Deb_Pack() {
    Check_apt_status
    
    ln -sf bash /bin/sh

    UBUNTU_22=$(cat /etc/issue|grep "Ubuntu 22")
    UBUNTU_24=$(cat /etc/issue|grep "Ubuntu 24")
    if [ "${UBUNTU_22}" ] || [ "${UBUNTU_24}" ];then
        apt-get remove needrestart -y
    fi
    apt-get update -y
    apt-get install bash -y
    if [ -f "/usr/bin/bash" ];then
        ln -sf /usr/bin/bash /bin/sh
    fi

    FNOS_CHECK=$(grep fnOS /etc/issue)
    if [ "${FNOS_CHECK}" ];then
        apt-get install libc6 -y --allow-change-held-packages
        apt-get install libc6-dev -y --allow-change-held-packages
    fi

    apt-get install ruby -y
    apt-get install lsb-release -y
    #apt-get install ntp ntpdate -y
    #/etc/init.d/ntp stop
    #update-rc.d ntp remove
    #cat >>~/.profile<<EOF
    #TZ='Asia/Shanghai'; export TZ
    #EOF
    #rm -rf /etc/localtime
    #cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
    #echo 'Synchronizing system time...'
    #ntpdate 0.asia.pool.ntp.org
    #apt-get upgrade -y
    LIBCURL_VER=$(dpkg -l | grep libcurl4 | awk '{print $3}')
    if [ "${LIBCURL_VER}" == "7.68.0-1ubuntu2.8" ]; then
        apt-get remove libcurl4 -y
        apt-get install curl -y
    fi

    debPacks="wget curl libcurl4-openssl-dev gcc make zip unzip tar openssl libssl-dev gcc libxml2 libxml2-dev libxslt-dev zlib1g zlib1g-dev libjpeg-dev libpng-dev lsof libpcre3 libpcre3-dev cron net-tools swig build-essential libffi-dev libbz2-dev libncurses-dev libsqlite3-dev libreadline-dev tk-dev libgdbm-dev libdb-dev libdb++-dev libpcap-dev xz-utils git ufw ipset sqlite3 uuid-dev libpq-dev liblzma-dev ca-certificates sudo autoconf at mariadb-client rsyslog xfsprogs quota libssh2-1-dev"

    DEBIAN_FRONTEND=noninteractive apt-get install -y $debPacks --allow-downgrades --allow-remove-essential --allow-change-held-packages

    for debPack in ${debPacks}; do
        packCheck=$(dpkg -l ${debPack})
        if [ "$?" -ne "0" ]; then
            DEBIAN_FRONTEND=noninteractive apt-get install -y $debPack --allow-downgrades --allow-remove-essential --allow-change-held-packages
        fi
    done
    if [ ! -d '/etc/letsencrypt' ]; then
        mkdir -p /etc/letsencryp
        mkdir -p /var/spool/cron
        if [ ! -f '/var/spool/cron/crontabs/root' ]; then
            echo '' >/var/spool/cron/crontabs/root
            chmod 600 /var/spool/cron/crontabs/root
        fi
    fi
}

Ubuntu_20_sources () {

cat > /etc/apt/sources.list << EOF
deb http://archive.ubuntu.com/ubuntu focal main restricted
# deb-src http://archive.ubuntu.com/ubuntu focal main restricted

deb http://ubuntu.mirror.constant.com focal main restricted
# deb-src http://ubuntu.mirror.constant.com focal main restricted

deb http://archive.ubuntu.com/ubuntu focal-updates main restricted
# deb-src http://archive.ubuntu.com/ubuntu focal-updates main restricted

deb http://ubuntu.mirror.constant.com focal-updates main restricted
# deb-src http://ubuntu.mirror.constant.com focal-updates main restricted

deb http://archive.ubuntu.com/ubuntu focal universe
# deb-src http://archive.ubuntu.com/ubuntu focal universe
deb http://archive.ubuntu.com/ubuntu focal-updates universe
# deb-src http://archive.ubuntu.com/ubuntu focal-updates universe

deb http://ubuntu.mirror.constant.com focal universe
# deb-src http://ubuntu.mirror.constant.com focal universe
deb http://ubuntu.mirror.constant.com focal-updates universe
# deb-src http://ubuntu.mirror.constant.com focal-updates universe

deb http://archive.ubuntu.com/ubuntu focal multiverse
# deb-src http://archive.ubuntu.com/ubuntu focal multiverse
deb http://archive.ubuntu.com/ubuntu focal-updates multiverse
# deb-src http://archive.ubuntu.com/ubuntu focal-updates multiverse

deb http://ubuntu.mirror.constant.com focal multiverse
# deb-src http://ubuntu.mirror.constant.com focal multiverse
deb http://ubuntu.mirror.constant.com focal-updates multiverse
# deb-src http://ubuntu.mirror.constant.com focal-updates multiverse

deb http://archive.ubuntu.com/ubuntu focal-backports main restricted universe multiverse
# deb-src http://archive.ubuntu.com/ubuntu focal-backports main restricted universe multiverse

deb http://ubuntu.mirror.constant.com focal-backports main restricted universe multiverse
# deb-src http://ubuntu.mirror.constant.com focal-backports main restricted universe multiverse

deb http://archive.ubuntu.com/ubuntu focal-security main restricted
# deb-src http://archive.ubuntu.com/ubuntu focal-security main restricted
deb http://archive.ubuntu.com/ubuntu focal-security universe
# deb-src http://archive.ubuntu.com/ubuntu focal-security universe
deb http://archive.ubuntu.com/ubuntu focal-security multiverse
# deb-src http://archive.ubuntu.com/ubuntu focal-security multiverse

deb http://ubuntu.mirror.constant.com focal-security main restricted
# deb-src http://ubuntu.mirror.constant.com focal-security main restricted
deb http://ubuntu.mirror.constant.com focal-security universe
# deb-src http://ubuntu.mirror.constant.com focal-security universe
deb http://ubuntu.mirror.constant.com focal-security multiverse
# deb-src http://ubuntu.mirror.constant.com focal-security multiverse

EOF

}

Ubuntu_22_sources () {

cat > /etc/apt/sources.list << EOF
deb http://archive.ubuntu.com/ubuntu jammy main restricted
# deb-src http://archive.ubuntu.com/ubuntu jammy main restricted

deb http://ubuntu.mirror.constant.com jammy main restricted
# deb-src http://ubuntu.mirror.constant.com jammy main restricted

deb http://archive.ubuntu.com/ubuntu jammy-updates main restricted
# deb-src http://archive.ubuntu.com/ubuntu jammy-updates main restricted

deb http://ubuntu.mirror.constant.com jammy-updates main restricted
# deb-src http://ubuntu.mirror.constant.com jammy-updates main restricted

deb http://archive.ubuntu.com/ubuntu jammy universe
# deb-src http://archive.ubuntu.com/ubuntu jammy universe
deb http://archive.ubuntu.com/ubuntu jammy-updates universe
# deb-src http://archive.ubuntu.com/ubuntu jammy-updates universe

deb http://ubuntu.mirror.constant.com jammy universe
# deb-src http://ubuntu.mirror.constant.com jammy universe
deb http://ubuntu.mirror.constant.com jammy-updates universe
# deb-src http://ubuntu.mirror.constant.com jammy-updates universe

deb http://archive.ubuntu.com/ubuntu jammy multiverse
# deb-src http://archive.ubuntu.com/ubuntu jammy multiverse
deb http://archive.ubuntu.com/ubuntu jammy-updates multiverse
# deb-src http://archive.ubuntu.com/ubuntu jammy-updates multiverse

deb http://ubuntu.mirror.constant.com jammy multiverse
# deb-src http://ubuntu.mirror.constant.com jammy multiverse
deb http://ubuntu.mirror.constant.com jammy-updates multiverse
# deb-src http://ubuntu.mirror.constant.com jammy-updates multiverse

deb http://archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse
# deb-src http://archive.ubuntu.com/ubuntu jammy-backports main restricted universe multiverse

deb http://ubuntu.mirror.constant.com jammy-backports main restricted universe multiverse
# deb-src http://ubuntu.mirror.constant.com jammy-backports main restricted universe multiverse

deb http://archive.ubuntu.com/ubuntu jammy-security main restricted
# deb-src http://archive.ubuntu.com/ubuntu jammy-security main restricted
deb http://archive.ubuntu.com/ubuntu jammy-security universe
# deb-src http://archive.ubuntu.com/ubuntu jammy-security universe
deb http://archive.ubuntu.com/ubuntu jammy-security multiverse
# deb-src http://archive.ubuntu.com/ubuntu jammy-security multiverse

deb http://ubuntu.mirror.constant.com jammy-security main restricted
# deb-src http://ubuntu.mirror.constant.com jammy-security main restricted
deb http://ubuntu.mirror.constant.com jammy-security universe
# deb-src http://ubuntu.mirror.constant.com jammy-security universe
deb http://ubuntu.mirror.constant.com jammy-security multiverse
# deb-src http://ubuntu.mirror.constant.com jammy-security multiverse

EOF

}


Ubuntu_24_sources () {

cat > /etc/apt/sources.list << EOF
deb http://archive.ubuntu.com/ubuntu noble main restricted
# deb-src http://archive.ubuntu.com/ubuntu noble main restricted

deb http://ubuntu.mirror.constant.com noble main restricted
# deb-src http://ubuntu.mirror.constant.com noble main restricted

deb http://archive.ubuntu.com/ubuntu noble-updates main restricted
# deb-src http://archive.ubuntu.com/ubuntu noble-updates main restricted

deb http://ubuntu.mirror.constant.com noble-updates main restricted
# deb-src http://ubuntu.mirror.constant.com noble-updates main restricted

deb http://archive.ubuntu.com/ubuntu noble universe
# deb-src http://archive.ubuntu.com/ubuntu noble universe
deb http://archive.ubuntu.com/ubuntu noble-updates universe
# deb-src http://archive.ubuntu.com/ubuntu noble-updates universe

deb http://ubuntu.mirror.constant.com noble universe
# deb-src http://ubuntu.mirror.constant.com noble universe
deb http://ubuntu.mirror.constant.com noble-updates universe
# deb-src http://ubuntu.mirror.constant.com noble-updates universe

deb http://archive.ubuntu.com/ubuntu noble multiverse
# deb-src http://archive.ubuntu.com/ubuntu noble multiverse
deb http://archive.ubuntu.com/ubuntu noble-updates multiverse
# deb-src http://archive.ubuntu.com/ubuntu noble-updates multiverse

deb http://ubuntu.mirror.constant.com noble multiverse
# deb-src http://ubuntu.mirror.constant.com noble multiverse
deb http://ubuntu.mirror.constant.com noble-updates multiverse
# deb-src http://ubuntu.mirror.constant.com noble-updates multiverse

deb http://archive.ubuntu.com/ubuntu noble-backports main restricted universe multiverse
# deb-src http://archive.ubuntu.com/ubuntu noble-backports main restricted universe multiverse

deb http://ubuntu.mirror.constant.com noble-backports main restricted universe multiverse
# deb-src http://ubuntu.mirror.constant.com noble-backports main restricted universe multiverse

deb http://archive.ubuntu.com/ubuntu noble-security main restricted
# deb-src http://archive.ubuntu.com/ubuntu noble-security main restricted
deb http://archive.ubuntu.com/ubuntu noble-security universe
# deb-src http://archive.ubuntu.com/ubuntu noble-security universe
deb http://archive.ubuntu.com/ubuntu noble-security multiverse
# deb-src http://archive.ubuntu.com/ubuntu noble-security multiverse

deb http://ubuntu.mirror.constant.com noble-security main restricted
# deb-src http://ubuntu.mirror.constant.com noble-security main restricted
deb http://ubuntu.mirror.constant.com noble-security universe
# deb-src http://ubuntu.mirror.constant.com noble-security universe
deb http://ubuntu.mirror.constant.com noble-security multiverse
# deb-src http://ubuntu.mirror.constant.com noble-security multiverse

EOF

}

Debian_11_sources () {

cat > /etc/apt/sources.list << EOF
deb https://deb.debian.org/debian bullseye main contrib non-free
deb-src https://deb.debian.org/debian bullseye main contrib non-free

deb https://deb.debian.org/debian-security/ bullseye-security main contrib non-free
deb-src https://deb.debian.org/debian-security/ bullseye-security main contrib non-free

deb https://deb.debian.org/debian bullseye-updates main contrib non-free
deb-src https://deb.debian.org/debian bullseye-updates main contrib non-free

#deb https://deb.debian.org/debian bullseye-backports main contrib non-free
#deb-src https://deb.debian.org/debian bullseye-backports main contrib non-free

deb https://debian.mirror.constant.com bullseye main contrib non-free
deb-src https://debian.mirror.constant.com bullseye main contrib non-free

EOF

}


Debian_12_sources () {

cat > /etc/apt/sources.list << EOF
deb https://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb-src https://deb.debian.org/debian bookworm main contrib non-free non-free-firmware

deb https://deb.debian.org/debian-security/ bookworm-security main contrib non-free non-free-firmware
deb-src https://deb.debian.org/debian-security/ bookworm-security main contrib non-free non-free-firmware

deb https://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
deb-src https://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware

#deb https://deb.debian.org/debian bookworm-backports main contrib non-free non-free-firmware
#deb-src https://deb.debian.org/debian bookworm-backports main contrib non-free non-free-firmware

deb https://debian.mirror.constant.com bookworm main contrib non-free non-free-firmware
deb-src https://debian.mirror.constant.com bookworm main contrib non-free non-free-firmware

EOF

}


Change_sources () {
    if [ -s /etc/os-release ] && [ -s /etc/issue ]; then
        . /etc/os-release
        echo "detected OS: $ID - $VERSION_ID"

        UD_os_version=$(cat /etc/issue | grep Ubuntu | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        OS_v=Ubuntu
        if [ "${UD_os_version}" = "" ]; then
            OS_v=Debian
            UD_os_version=$(cat /etc/issue | grep Debian | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '[0-9]+')
            if [ "${UD_os_version}" = "" ]; then
                UD_os_version=$(cat /etc/issue | grep Debian | grep -Eo '[0-9]+')
            fi
        fi
        echo "detected OS version: $OS_v $UD_os_version"

        if [ $ID == "debian" ] && [ $OS_v == "Debian" ]; then
            if [ $VERSION_ID == "11" ] && [ $UD_os_version == "11" ]; then
                Debian_11_sources
            elif [ $VERSION_ID == "12" ] && [ $UD_os_version == "12" ]; then
                Debian_12_sources
            else
                echo -e "\033[31mSorry: $OS_v $UD_os_version This system does not support changing apt source, please try to change it yourself. \033[0m"
                Change_apt_sources="no"
            fi

        elif [ $ID == "ubuntu" ] && [ $OS_v == "Ubuntu" ]; then
            if [ `echo "$VERSION_ID" | cut -b-2 ` == "20" ] && [ $UD_os_version == "20" ]; then
                Ubuntu_20_sources
            elif [ `echo "$VERSION_ID" | cut -b-2 ` == "22" ] && [ $UD_os_version == "22" ]; then
                Ubuntu_22_sources
            elif [ `echo "$VERSION_ID" | cut -b-2 ` == "24" ] && [ $UD_os_version == "24" ]; then
                Ubuntu_24_sources
            else
                echo -e "\033[31mSorry: $OS_v $UD_os_version This system does not support changing apt source, please try to change it yourself. \033[0m"
                Change_apt_sources="no"
            fi
        else
            echo -e "\033[31mSorry: $OS_v $UD_os_version This system does not support changing apt source, please try to change it yourself. \033[0m"
            Change_apt_sources="no"
        fi

    fi
}

Check_Change_official_sources () {
    if [ -s /etc/apt/sources.list ]; then
        ubuntu_sources=$(grep "\.ubuntu\.com" /etc/apt/sources.list | grep -v '^#' | grep -v "security\.ubuntu\.com")
        debian_sources=$(grep "\.debian\.org" /etc/apt/sources.list | grep -v '^#' | grep -v "security\.debian\.org")

        if [ "$ubuntu_sources" = "" ] && [ "$debian_sources" = "" ]; then
            while [ "$yes2" != 'yes' ] && [ "$yes2" != 'no' ]; do
                read -p "Found that apt source cannot be used. Do need to change it to the official source? [yes/no] " yes2
            done
            if [ "$yes2" = "yes" ]; then

                Backup_sources_time=$(date +%Y_%m_%d_%H_%M_%S)
                cp -arpf /etc/apt/sources.list /etc/apt/sources.list_aapanel_${Backup_sources_time}
                echo -e "The sources.list file has been backup. The backup file name is:\033[31m /etc/apt/sources.list_aapanel_${Backup_sources_time} \033[0m"

                Change_sources

                if [ "${Change_apt_sources}" != "no" ]; then
                    Install_Deb_Pack
                fi

            fi
        fi
    fi
}


Check_Install_Sys_Packs() {
    echo "Checking necessary dependency system packages"
    # Define functions for installation packages
    install_package() {
        local package=$1
        if [ "${PM}" = "yum" ]; then
            yum install "$package" -y
        elif [ "${PM}" = "apt-get" ]; then
            dpkg --configure -a
            apt-get update
            apt-get install "$package" -y
        fi
    }

    # Define a function to install and verify
    install_and_verify() {
        local package_name=$1
        local command_name=$2

        # First try installing directly
        if ! Command_Exists "$command_name"; then
            install_package "$package_name"
        fi

        # try change official sources
        if [ ! -f "/usr/bin/$command_name" ] && [ ! -f "/bin/$command_name" ] && ! Command_Exists "$command_name"; then
            Check_Change_official_sources
        fi

        # Check again, if it is still missing, an error message will be reported.
        if [ ! -f "/usr/bin/$command_name" ] && [ ! -f "/bin/$command_name" ] && ! Command_Exists "$command_name"; then
            echo -e "\033[31mERROR: "$command_name" command does not exist, try the following solutions:\033[0m"
            echo -e "1. Use command reinstall dependent packages: \033[31m ${PM} reinstall -y $package_name \033[0m"
            echo -e "2. Check if system source is available? Try changing available system sources"
            echo -e "After solving the above problems, please try to reinstall!"
            if [ -s /etc/apt/sources.list ]; then
                Vive_source=$(grep -v '^#' /etc/apt/sources.list | grep -Ev "^\s*$|security\.ubuntu\.com|security\.debian\.org" | head -n 1)
                Vive_source="apt source: $Vive_source"
                # echo "$Vive_source"
            fi
            Red_Error "Error: $command_name command not found, please install $package_name command. $Vive_source"
        fi
    }

    # Install and check unzip
    install_and_verify "unzip" "unzip"

    # Install and check tar
    install_and_verify "tar" "tar"

    # Install and check wget
    install_and_verify "wget" "wget"
}

Get_Versions() {
    redhat_version_file="/etc/redhat-release"
    deb_version_file="/etc/issue"

    if [[ $(grep "Amazon Linux" /etc/os-release) ]]; then
        os_type="Amazon-"
        os_version=$(cat /etc/os-release | grep "Amazon Linux" | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        yum install cronie -y
        return
    fi

    if [[ $(grep OpenCloudOS /etc/os-release) ]]; then
        os_type="OpenCloudOS-"
        os_version=$(cat /etc/os-release | grep OpenCloudOS | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        if [[ $os_version == "7" ]]; then
            os_type="el"
            os_version="7"
        fi 
        return
    fi

    if [[ $(grep "Linux Mint" $deb_version_file) ]]; then
        os_version=$(cat $deb_version_file | grep "Linux Mint" | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        if [ "${os_version}" = "" ]; then
            os_version=$(cat $deb_version_file | grep "Linux Mint" | grep -Eo '[0-9]+')
        fi
        # Linux-Mint using ubuntu pyenv
        os_type='ubuntu'
        if [[ "$os_version" =~ "21" ]]; then
            os_version="22"
            echo "$os_version"
        fi
        if [[ "$os_version" =~ "20" ]]; then
            os_version="20"
            echo "$os_version"
        fi
        return
    fi

    if [[ $(grep openEuler /etc/os-release) ]]; then
        os_type="openEuler-"
        os_version=$(cat /etc/os-release | grep openEuler | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        return
    fi

    if [[ $(grep AlmaLinux /etc/os-release) ]]; then
        os_type="Alma-"
        os_version=$(cat /etc/os-release | grep AlmaLinux | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        return
    fi

    if [[ $(grep Rocky /etc/os-release) ]]; then
        os_type="Rocky-"
        os_version=$(cat /etc/os-release | grep Rocky | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        return
    fi

    if [[ $(grep Anolis /etc/os-release) ]] && [[ $(grep VERSION /etc/os-release|grep 8.8) ]];then
        if [ -f "/usr/bin/yum" ];then
            os_type="anolis"
            os_version="8"
            return
        fi
    fi        

    if [ -s $redhat_version_file ]; then
        os_type='el'
        if [[ $(grep 'Alibaba Cloud Linux (Aliyun Linux) release 2' $redhat_version_file) ]]; then
            os_version="7"
            return
        fi

        is_aliyunos=$(cat $redhat_version_file | grep Aliyun)
        if [ "$is_aliyunos" != "" ]; then
            return
        fi

        if [[ $(grep "Red Hat" $redhat_version_file) ]]; then
            os_type='el'
            os_version=$(cat $redhat_version_file | grep "Red Hat" | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]')
            return
        fi

        if [[ $(grep "Alibaba Cloud Linux release 3 " /etc/redhat-release) ]]; then
            os_type="ali-linux-"
            os_version="3"
            return
        fi

        if [[ $(grep "Alibaba Cloud" /etc/redhat-release) ]] && [[ $(grep al8 /etc/os-release) ]];then
            os_type="ali-linux-"
            os_version="al8"
            return
        fi

        if [[ $(grep TencentOS /etc/redhat-release) ]]; then
            os_type="TencentOS-"
            os_version=$(cat /etc/redhat-release | grep TencentOS | grep -Eo '([0-9]+\.)+[0-9]+')
            if [[ $os_version == "2.4" ]]; then
                os_type="el"
                os_version="7"
            elif [[ $os_version == "3.1" ]]; then
                os_version="3.1"
            fi
            return
        fi

        os_version=$(cat $redhat_version_file | grep CentOS | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]')
        if [ "${os_version}" = "5" ]; then
            os_version=""
        fi
        if [ -z "${os_version}" ]; then
            os_version=$(cat /etc/redhat-release | grep Stream | grep -oE "8|9|10")
        fi
    else
        os_type='ubuntu'
        os_version=$(cat $deb_version_file | grep Ubuntu | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '^[0-9]+')
        if [ "${os_version}" = "" ]; then
            os_type='debian'
            os_version=$(cat $deb_version_file | grep Debian | grep -Eo '([0-9]+\.)+[0-9]+' | grep -Eo '[0-9]+')
            if [ "${os_version}" = "" ]; then
                os_version=$(cat $deb_version_file | grep Debian | grep -Eo '[0-9]+')
            fi
            if [ "${os_version}" = "8" ]; then
                os_version=""
            fi
            if [ "${is64bit}" = '32' ]; then
                os_version=""
            fi
        else
            if [ "$os_version" = "14" ]; then
                os_version=""
            fi
            if [ "$os_version" = "12" ]; then
                os_version=""
            fi
            if [ "$os_version" = "19" ]; then
                os_version=""
            fi
            if [ "$os_version" = "21" ]; then
                os_version=""
            fi
            if [ "$os_version" = "20" ]; then
                os_version2004=$(cat /etc/issue | grep 20.04)
                if [ -z "${os_version2004}" ]; then
                    os_version=""
                fi
            fi
        fi
    fi
}

Install_Openssl111(){
    Get_Versions
    if [ -f "/www/server/panel/openssl_make.pl" ]; then
        # 存在时编译
        openssl_make="yes"
        rm -f /www/server/panel/openssl_make.pl
    fi

    CPU_arch=$(uname -m)
    if [ "${CPU_arch}" == "aarch64" ];then
        CPU_arch="-aarch64"
    elif [ "${CPU_arch}" == "x86_64" ];then
        # x86_64 默认为空
        CPU_arch=""
    else
        openssl_make="yes"
    fi

    if [[ $os_type = "el" ]] && [[ $os_version == "7" ]] && [[ $openssl_make != "yes" ]]; then
        wget --no-check-certificate -O openssl111.tar.gz ${download_Url}/install/src/openssl111${CPU_arch}.tar.gz -t 5 -T 20
        tmp_size=$(du -b openssl111.tar.gz | awk '{print $1}')
        if [ $tmp_size -lt 5014046 ]; then
            rm -f openssl111.tar.gz
            Red_Error "ERROR: Download openssl111.tar.gz fielded."
        fi
        tar zxvf openssl111.tar.gz -C /usr/local/
        rm -f openssl111.tar.gz
        if [ ! -f "/usr/local/openssl111/bin/openssl" ];then
            Red_Error "/usr/local/openssl111/bin/openssl file does not exist!"
        fi
        export LD_LIBRARY_PATH=/usr/local/openssl111/lib:$LD_LIBRARY_PATH
        echo "/usr/local/openssl111/lib" > /etc/ld.so.conf.d/zopenssl111.conf
        ldconfig
    else
        if [ -f "/usr/bin/yum" ] && [ -d "/etc/yum.repos.d" ]; then
            yum install -y perl lksctp-tools-devel
        else
            apt install -y perl
        fi
        opensslVersion="1.1.1o"
        wget --no-check-certificate -O openssl-${opensslVersion}.tar.gz ${download_Url}/src/openssl-${opensslVersion}.tar.gz -t 5 -T 20
        tmp_size=$(du -b openssl-${opensslVersion}.tar.gz | awk '{print $1}')
        if [ $tmp_size -lt 9056386 ]; then
            rm -f openssl-${opensslVersion}.tar.gz
            Red_Error "ERROR: Download openssl-${opensslVersion}.tar.gz fielded."
        fi
        tar -zxvf openssl-${opensslVersion}.tar.gz
        if [ ! -d "openssl-${opensslVersion}" ];then
            Red_Error "Decompression failed openssl-${opensslVersion} Directory does not exist!"
        fi
        cd openssl-${opensslVersion}
        ./config --prefix=/usr/local/openssl111 --openssldir=/usr/local/openssl111 enable-md2 enable-rc5 sctp zlib-dynamic shared -fPIC
        make -j$cpu_cpunt
        make install
        if [ ! -f "/usr/local/openssl111/bin/openssl" ];then
            Red_Error "Compilation failed /usr/local/openssl111/bin/openssl file does not exist!"
        fi
        export LD_LIBRARY_PATH=/usr/local/openssl111/lib:$LD_LIBRARY_PATH
        echo "/usr/local/openssl111/lib" > /etc/ld.so.conf.d/zopenssl111.conf
        ldconfig
        cd ..
        rm -rf openssl-${opensslVersion} openssl-${opensslVersion}.tar.gz
    fi
    openssl111Check=$(/usr/local/openssl111/bin/openssl version|grep 1.1.1)
    if [ -z "${openssl111Check}" ];then
        Red_Error "openssl-1.1.1 install failed!"
    fi
}

Update_Py_Lib(){
# Need to use Werkzeug 2.2.3
    mypip="/www/server/panel/pyenv/bin/pip3"
    Werkzeug_path="/www/server/panel/script/Werkzeug-2.2.3-py3-none-any.whl"
    pycountry_path="/www/server/panel/script/pycountry-24.6.1-py3-none-any.whl"
    # pyOpenSSL_path="/www/server/panel/script/pyOpenSSL-23.1.1-py3-none-any.whl"

    change_pip_package_list=$( $mypip list | grep -E "Werkzeug|lxml|pycountry" )
    #change_pip_package_list=$( $mypip list | grep -E "Werkzeug|lxml" )
    
    Werkzeug_v=$(echo "$change_pip_package_list" | grep Werkzeug | grep 2.2.3)
    if [ "$Werkzeug_v" = "" ];then
        echo "Update Werkzeug"
        $mypip uninstall Werkzeug -y 
        $mypip install $Werkzeug_path

        Werkzeug_v_2=$($mypip list |grep Werkzeug | grep 2.2.3)
        if [ "$Werkzeug_v_2" = "" ];then
            $mypip install Werkzeug==2.2.3
        fi
    fi

    pycountry_v=$(echo "$change_pip_package_list" | grep pycountry)
    if [ "$pycountry_v" = "" ];then
        echo "Update pycountry"
        $mypip install $pycountry_path
        rm -f $pycountry_path

        pycountry_v_2=$($mypip list |grep pycountry)
        if [ "$pycountry_v_2" = "" ];then
            $mypip install pycountry
        fi
    fi

    # pyOpenSSL_v=$(echo "$change_pip_package_list" | grep pyOpenSSL | grep 23.1.1)
    # if [ "$pyOpenSSL_v" = "" ];then
    #     echo "Update pyOpenSSL"
    #     $mypip uninstall pyOpenSSL cryptography -y 
    #     $mypip install $pyOpenSSL_path cryptography==40.0.2

    #     pyOpenSSL_v_2=$($mypip list |grep pyOpenSSL | grep 23.1.1)
    #     if [ "$pyOpenSSL_v_2" = "" ];then
    #         $mypip install pyOpenSSL==23.1.1 cryptography==40.0.2
    #     fi
    # fi

    lxml_v=$(echo "$change_pip_package_list" | grep lxml | grep 5.2.1)
    if [ "$lxml_v" != "" ];then
        echo "Update lxml"
        $mypip uninstall lxml -y
        # bt 16 升级脚本时安装，安装时间久 这里不开，下面进行处理了
        # echo "Please wait a moment to install lxml, it will take a long time."
        # $mypip install lxml==5.0.0

        # lxml_v_2=$($mypip list |grep lxml | grep 5.2.1)
        # if [ "$lxml_v_2" = "" ];then
        #     $mypip install lxml==5.0.0
        # fi
    fi

}

Check_PIP_Packages(){

    mypip="/www/server/panel/pyenv/bin/pip3"
    show_pip_list_panel="/tmp/show_pip_list_panel.txt"
    
    trusted_host="--trusted-host mirrors.tencent.com --trusted-host pypi.doubanio.com --trusted-host mirrors.aliyun.com --trusted-host pypi.tuna.tsinghua.edu.cn --trusted-host pypi.org"
    
    echo "Check pip package, please wait..."

    ${mypip} list | awk '{print $1}' > ${show_pip_list_panel}
    
    check_pip_packs="/www/server/panel/check-pip-packs.txt"
    if [ ! -s "${check_pip_packs}" ]; then
        check_pip_packs="/tmp/check-pip-packs_3.12.txt"
        wget --no-check-certificate -O ${check_pip_packs} ${download_Url}/install/pyenv/3.12/check-pip-packs_3.12.txt -t 5 -T 20
    fi

    Install_PIP_PACKS_File="/www/server/panel/requirements.txt"
    if [ ! -s "${Install_PIP_PACKS_File}" ]; then
        Install_PIP_PACKS_File="/tmp/pip_en_3.12.txt"
        wget --no-check-certificate -O ${Install_PIP_PACKS_File} ${download_Url}/install/pyenv/3.12/pip_en_3.12.txt -t 5 -T 20
    fi
    
    PIP_PACKS=$(cat ${check_pip_packs} )
    for ONE_PACK in ${PIP_PACKS};
    do
        Install_PIP_PACKS=`grep "^${ONE_PACK}==" ${Install_PIP_PACKS_File}`
        if [ -z "${Install_PIP_PACKS}" ]; then
            Install_PIP_PACKS=${ONE_PACK}
        fi
        Show_PIP_PACK=`grep "^${ONE_PACK}\$" ${show_pip_list_panel}`
        # echo ${Show_PIP_PACK}
        if [ -z "${Show_PIP_PACK}" ];then
            if [[ "${ONE_PACK}" == "aliyun-python-sdk-kms" || "${ONE_PACK}" == "aliyun-python-sdk-core" || "${ONE_PACK}" == "aliyun-python-sdk-core-v3" || "${ONE_PACK}" == "qiniu" || "${ONE_PACK}" == "cos-python-sdk-v5" ]]; then
                echo "Install packages: ${Install_PIP_PACKS}" >/dev/null 2>&1
            else
                echo "Install packages: ${Install_PIP_PACKS}"
            fi

            if [[ "${ONE_PACK}" == "Flask" ]]; then
                ${mypip} uninstall Flask Werkzeug -y
                ${mypip} install Flask==2.2.5 Werkzeug==2.2.3 ${trusted_host}
            elif [[ "${ONE_PACK}" == "Werkzeug" ]]; then
                ${mypip} install Werkzeug==2.2.3 ${trusted_host}  
            elif [[ "${ONE_PACK}" == "aliyun-python-sdk-kms" || "${ONE_PACK}" == "aliyun-python-sdk-core" || "${ONE_PACK}" == "aliyun-python-sdk-core-v3" || "${ONE_PACK}" == "qiniu" || "${ONE_PACK}" == "cos-python-sdk-v5" ]]; then
                echo "${Install_PIP_PACKS} ..."  >/dev/null 2>&1
            else
                ${mypip} install ${Install_PIP_PACKS} ${trusted_host}
            fi
        fi  
    done

}

Install_Python_Lib() {

    # openssl 版本低于1.1.1 需要安装 如CentOS 7
    OPENSSL_VER=$(openssl version|grep -oE '1.0|1.1.0')
    if [ "${OPENSSL_VER}" ]; then
        
        if [ ! -f "/usr/local/openssl111/bin/openssl" ]; then
            Install_Openssl111
        else
            export LD_LIBRARY_PATH=/usr/local/openssl111/lib:$LD_LIBRARY_PATH
            openssl111Check=$(/usr/local/openssl111/bin/openssl version|grep 1.1.1)
            if [ -z "${openssl111Check}" ];then
                Install_Openssl111
            fi
            if [ ! -f "/etc/ld.so.conf.d/openssl111.conf" ] || [ ! -f "/etc/ld.so.conf.d/zopenssl111.conf" ]; then
                echo "/usr/local/openssl111/lib" > /etc/ld.so.conf.d/zopenssl111.conf
                ldconfig
            fi
        fi
        Use_Openssl111="yes"
    fi

    curl -sSk --connect-timeout 5 -m 60 $download_Url/install/pip_select.sh | bash
    pyenv_path="/www/server/panel"
    if [ -f $pyenv_path/pyenv/bin/python ]; then
        is_ssl=$($python_bin -c "import ssl" 2>&1 | grep cannot)
        $pyenv_path/pyenv/bin/python3.12 -V
        if [ $? -eq 0 ] && [ -z "${is_ssl}" ]; then
            chmod -R 700 $pyenv_path/pyenv/bin
            is_package=$($python_bin -m psutil 2>&1 | grep package)
            if [ "$is_package" = "" ]; then
                wget --no-check-certificate -O $pyenv_path/pyenv/pip.txt $download_Url/install/pyenv/3.12/pip_en_3.12.txt -t 5 -T 20
                $pyenv_path/pyenv/bin/pip install -U pip
                $pyenv_path/pyenv/bin/pip install -U setuptools
                $pyenv_path/pyenv/bin/pip install -r $pyenv_path/pyenv/pip.txt
            fi
            source $pyenv_path/pyenv/bin/activate
            chmod -R 700 $pyenv_path/pyenv/bin
            return
        else
            rm -rf $pyenv_path/pyenv
        fi
    fi

    is_loongarch64=$(uname -a | grep loongarch64)
    if [ "$is_loongarch64" != "" ] && [ -f "/usr/bin/yum" ]; then
        yumPacks="python3-devel python3-pip python3-psutil python3-gevent python3-pyOpenSSL python3-paramiko python3-flask python3-rsa python3-requests python3-six python3-websocket-client"
        yum install -y ${yumPacks}
        for yumPack in ${yumPacks}; do
            rpmPack=$(rpm -q ${yumPack})
            packCheck=$(echo ${rpmPack} | grep not)
            if [ "${packCheck}" ]; then
                yum install ${yumPack} -y
            fi
        done

        pip3 install -U pip
        pip3 install Pillow psutil pyinotify pycryptodome upyun oss2 pymysql qrcode qiniu redis pymongo Cython configparser cos-python-sdk-v5 supervisor gevent-websocket pyopenssl
        pip3 install flask==1.1.4
        pip3 install Pillow -U

        pyenv_bin=/www/server/panel/pyenv/bin
        mkdir -p $pyenv_bin
        ln -sf /usr/local/bin/pip3 $pyenv_bin/pip
        ln -sf /usr/local/bin/pip3 $pyenv_bin/pip3
        ln -sf /usr/local/bin/pip3 $pyenv_bin/pip3.7

        if [ -f "/usr/bin/python3.7" ]; then
            ln -sf /usr/bin/python3.7 $pyenv_bin/python
            ln -sf /usr/bin/python3.7 $pyenv_bin/python3
            ln -sf /usr/bin/python3.7 $pyenv_bin/python3.7
        elif [ -f "/usr/bin/python3.6" ]; then
            ln -sf /usr/bin/python3.6 $pyenv_bin/python
            ln -sf /usr/bin/python3.6 $pyenv_bin/python3
            ln -sf /usr/bin/python3.6 $pyenv_bin/python3.7
        fi

        echo >$pyenv_bin/activate

        return
    fi

    py_version="3.12.3"
    python_version="-3.12"
    mkdir -p $pyenv_path
    echo "True" >/www/disk.pl
    if [ ! -w /www/disk.pl ]; then
        Red_Error "ERROR: Install python env fielded." "ERROR: path [www] cannot be written, please check the directory/user/disk permissions!"
    fi
    os_type='el'
    os_version='7'
    is_export_openssl=0
    Get_Versions
    echo "OS: $os_type - $os_version"
    is_aarch64=$(uname -m | grep aarch64)
    if [ "$is_aarch64" != "" ]; then
        is64bit="aarch64"
    fi
    if [ -f "/www/server/panel/pymake.pl" ]; then
        os_version=""
        rm -f /www/server/panel/pymake.pl
    fi
    if [ "${os_version}" != "" ]; then
        pyenv_file="/www/pyenv.tar.gz"
        wget --no-check-certificate -O $pyenv_file $download_Url/install/pyenv/3.12/pyenv-${os_type}${os_version}-x${is64bit}${python_version}.tar.gz -t 5 -T 20
        if [ "$?" != "0" ];then
            get_node_url $download_Url
            wget --no-check-certificate -O $pyenv_file $download_Url/install/pyenv/3.12/pyenv-${os_type}${os_version}-x${is64bit}${python_version}.tar.gz -t 5 -T 20
        fi
        tmp_size=$(du -b $pyenv_file | awk '{print $1}')
        if [ $tmp_size -lt 122271175 ]; then
            rm -f $pyenv_file
            echo "ERROR: Download python env fielded."
        else
            echo "Install python env..."
            tar zxvf $pyenv_file -C $pyenv_path/ >/dev/null
            chmod -R 700 $pyenv_path/pyenv/bin
            if [ ! -f $pyenv_path/pyenv/bin/python ]; then
                rm -f $pyenv_file
                Red_Error "ERROR: Install python env fielded. Please try to reinstall"
            fi
            $pyenv_path/pyenv/bin/python3.12 -V
            if [ $? -eq 0 ]; then
                rm -f $pyenv_file
                ln -sf $pyenv_path/pyenv/bin/pip3.12 /usr/bin/btpip
                ln -sf $pyenv_path/pyenv/bin/python3.12 /usr/bin/btpython
                source $pyenv_path/pyenv/bin/activate
                return
            else
                rm -f $pyenv_file
                rm -rf $pyenv_path/pyenv
            fi
        fi
    fi

    cd /www
    python_src='/www/python_src.tar.xz'
    python_src_path="/www/Python-${py_version}"
    wget --no-check-certificate -O $python_src $download_Url/src/Python-${py_version}.tar.xz -t 5 -T 20
    tmp_size=$(du -b $python_src | awk '{print $1}')
    if [ $tmp_size -lt 10703460 ]; then
        rm -f $python_src
        Red_Error "ERROR: Download python source code fielded. Please try to reinstall OS_${os_type}_${os_version}."
    fi
    tar xvf $python_src
    rm -f $python_src
    cd $python_src_path
    if [[ $Use_Openssl111 = "yes" ]]; then
        # centos7 或者低openssl于1.1.1使用
        export OPENSSL_DIR=/usr/local/openssl111
        ./configure --prefix=$pyenv_path/pyenv \
        LDFLAGS="-L$OPENSSL_DIR/lib" \
        CPPFLAGS="-I$OPENSSL_DIR/include" \
        --with-openssl=$OPENSSL_DIR
    else
        ./configure --prefix=$pyenv_path/pyenv
    fi

    make -j$cpu_cpunt
    make install
    if [ ! -f $pyenv_path/pyenv/bin/python3.12 ]; then
        rm -rf $python_src_path
        Red_Error "ERROR: Make python env fielded. Please try to reinstall"
    fi
    cd ~
    rm -rf $python_src_path
    wget --no-check-certificate -O $pyenv_path/pyenv/bin/activate $download_Url/install/pyenv/activate.panel -t 5 -T 20
    wget --no-check-certificate -O $pyenv_path/pyenv/pip.txt $download_Url/install/pyenv/3.12/pip-3.12.3.txt -t 5 -T 20
    ln -sf $pyenv_path/pyenv/bin/pip3.12 $pyenv_path/pyenv/bin/pip
    ln -sf $pyenv_path/pyenv/bin/python3.12 $pyenv_path/pyenv/bin/python
    ln -sf $pyenv_path/pyenv/bin/pip3.12 /usr/bin/btpip
    ln -sf $pyenv_path/pyenv/bin/python3.12 /usr/bin/btpython
    chmod -R 700 $pyenv_path/pyenv/bin
    $pyenv_path/pyenv/bin/pip install -U pip
    $pyenv_path/pyenv/bin/pip install -U setuptools
    # $pyenv_path/pyenv/bin/pip install -U wheel==0.34.2
    $pyenv_path/pyenv/bin/pip install -r $pyenv_path/pyenv/pip.txt

    source $pyenv_path/pyenv/bin/activate
    btpip install psutil
    btpip install gevent
    is_gevent=$($python_bin -m gevent 2>&1 | grep -oE package)
    is_psutil=$($python_bin -m psutil 2>&1 | grep -oE package)
    if [ "${is_gevent}" != "${is_psutil}" ]; then
        Check_PIP_Packages
        is_gevent=$($python_bin -m gevent 2>&1 | grep -oE package)
        is_psutil=$($python_bin -m psutil 2>&1 | grep -oE package)
        if [ "${is_gevent}" != "${is_psutil}" ]; then
            Red_Error "ERROR: psutil/gevent install failed!"
        fi
    fi
}

delete_useless_package() {
    /www/server/panel/pyenv/bin/pip uninstall aliyun-python-sdk-kms -y >/dev/null 2>&1
    /www/server/panel/pyenv/bin/pip uninstall aliyun-python-sdk-core -y >/dev/null 2>&1
    /www/server/panel/pyenv/bin/pip uninstall aliyun-python-sdk-core-v3 -y >/dev/null 2>&1
    /www/server/panel/pyenv/bin/pip uninstall qiniu -y >/dev/null 2>&1
    /www/server/panel/pyenv/bin/pip uninstall cos-python-sdk-v5 -y >/dev/null 2>&1
}

Install_Bt() {
    if [ -f ${setup_path}/server/panel/data/port.pl ]; then
        panelPort=$(cat ${setup_path}/server/panel/data/port.pl)
    fi

	if [ "${PANEL_PORT}" ];then
		panelPort=$PANEL_PORT
	fi
    
    mkdir -p ${setup_path}/server/panel/logs
    mkdir -p ${setup_path}/server/panel/vhost/apache
    mkdir -p ${setup_path}/server/panel/vhost/nginx
    mkdir -p ${setup_path}/server/panel/vhost/rewrite
    mkdir -p ${setup_path}/server/panel/install
    mkdir -p /www/server
    mkdir -p /www/wwwroot
    mkdir -p /www/wwwlogs
    mkdir -p /www/backup/database
    mkdir -p /www/backup/site

    if [ ! -d "/etc/init.d" ];then
        mkdir -p /etc/init.d
    fi

    if [ -f "/etc/init.d/bt" ]; then
        /etc/init.d/bt stop
        sleep 1
    fi

    panel_file="${setup_path}/panel.zip"
    wget --no-check-certificate -O ${panel_file} ${download_Url}/install/src/panel_7_en.zip -t 5 -T 20

    tmp_size=$(du -b ${panel_file} | awk '{print $1}')
    if [ $tmp_size -lt 10026905 ]; then
        ls -lh ${panel_file}
        rm -f ${panel_file}
        Red_Error "ERROR: Failed to download panel, please try install again!"
    fi
    
    # wget --no-check-certificate -O /etc/init.d/bt ${download_Url}/install/src/bt7_en.init -t 5 -T 20
    # wget --no-check-certificate -O /www/server/panel/init.sh ${download_Url}/install/src/bt7_en.init -t 5 -T 20
    wget --no-check-certificate -O /www/server/panel/install/public.sh ${download_Url}/install/public.sh -t 5 -T 20

    if [ -f "${setup_path}/server/panel/data/default.db" ]; then
        if [ -d "/${setup_path}/server/panel/old_data" ]; then
            rm -rf ${setup_path}/server/panel/old_data
        fi
        mkdir -p ${setup_path}/server/panel/old_data
        d_format=$(date +"%Y%m%d_%H%M%S")
        \cp -arf ${setup_path}/server/panel/data/default.db ${setup_path}/server/panel/data/default_backup_${d_format}.db
        mv -f ${setup_path}/server/panel/data/default.db ${setup_path}/server/panel/old_data/default.db
        mv -f ${setup_path}/server/panel/data/system.db ${setup_path}/server/panel/old_data/system.db
        mv -f ${setup_path}/server/panel/data/port.pl ${setup_path}/server/panel/old_data/port.pl
        mv -f ${setup_path}/server/panel/data/admin_path.pl ${setup_path}/server/panel/old_data/admin_path.pl
    fi

    unzip -o ${panel_file} -d ${setup_path}/server/ >/dev/null

    if [ -d "${setup_path}/server/panel/old_data" ]; then
        mv -f ${setup_path}/server/panel/old_data/default.db ${setup_path}/server/panel/data/default.db
        mv -f ${setup_path}/server/panel/old_data/system.db ${setup_path}/server/panel/data/system.db
        mv -f ${setup_path}/server/panel/old_data/port.pl ${setup_path}/server/panel/data/port.pl
        mv -f ${setup_path}/server/panel/old_data/admin_path.pl ${setup_path}/server/panel/data/admin_path.pl
        if [ -d "/${setup_path}/server/panel/old_data" ]; then
            rm -rf ${setup_path}/server/panel/old_data
        fi
    fi
    
    if [ ! -f "${setup_path}/server/panel/tools.py" ] || [ ! -f "${setup_path}/server/panel/BT-Panel" ]; then
        ls -lh ${setup_path}/server/panel/BT-* ${setup_path}/server/panel/tools.py
        Red_Error "ERROR: tools.py BT-Panel file does not exist, please try install again!"
    fi

    Check_PIP_Packages
    delete_useless_package
    Update_Py_Lib
    rm -f ${panel_file}
    rm -f ${setup_path}/server/panel/class/*.pyc
    rm -f ${setup_path}/server/panel/*.pyc

    \cp -arpf /www/server/panel/init.sh /etc/init.d/bt
    if [[ ! -s "/etc/init.d/bt" ]];then
        rm -f /etc/init.d/bt
        wget --no-check-certificate -O /etc/init.d/bt ${download_Url}/install/src/bt7_en.init -t 5 -T 20
        wget --no-check-certificate -O /www/server/panel/init.sh ${download_Url}/install/src/bt7_en.init -t 5 -T 20
        if [[ ! -s "/etc/init.d/bt" ]];then
            Red_Error "ERROR: /etc/init.d/bt file content is 0kb "
        fi
    fi
    chmod +x /etc/init.d/bt
    chmod -R 600 ${setup_path}/server/panel
    chmod -R 755 ${setup_path}/server/panel/webserver
    chmod -R +x ${setup_path}/server/panel/script
    ln -sf /etc/init.d/bt /usr/bin/bt
    echo "${panelPort}" >${setup_path}/server/panel/data/port.pl
    wget --no-check-certificate -O /www/server/panel/data/softList.conf ${download_Url}/install/conf/softList_en.conf -t 5 -T 20
}

Use_self_signed_certificate() {
    echo "Use Self-signed certificate"
    rm -f /www/server/panel/ssl/*
    SSL_path=/www/server/panel/ssl
    # Create private key
    openssl genrsa -out ${SSL_path}/privateKey.pem 2048

    # Create a self-signed root certificate
    openssl req -x509 -new -nodes -key ${SSL_path}/privateKey.pem -sha256 -days 3650 -out ${SSL_path}/certificate.pem \
    -subj "/C=US/ST=State/L=City/O=aapanel.com/OU=aapanel.com/CN=*.aapanel.com" -nodes
    
    # Use random password
    # SSL_password=$(cat /dev/urandom | head -n 16 | md5sum | head -c 16)

    # Create PFX file
    # openssl pkcs12 -export -out ${SSL_path}/baota_root.pfx -inkey ${SSL_path}/privateKey.pem -in ${SSL_path}/certificate.pem -passout pass:${SSL_password}

    # Create password file
    # echo "${SSL_password}" > ${SSL_path}/root_password.pl

    echo "True" > /www/server/panel/data/ssl.pl
    SET_SSL=true

    if [ ! -s "${SSL_path}/privateKey.pem" ] || [ ! -s "${SSL_path}/certificate.pem" ]; then
        SET_SSL=false
        rm -f /www/server/panel/data/ssl.pl
        echo "Self-signed certificate failed, panel SSl closed"
    fi
}

Set_Bt_Panel() {
    Run_User="www"
	wwwUser=$(cat /etc/passwd|cut -d ":" -f 1|grep ^www$)
	if [ "${wwwUser}" != "www" ];then
		groupadd ${Run_User}
		useradd -s /sbin/nologin -g ${Run_User} ${Run_User}
	fi
    chmod -R 700 /www/server/panel/pyenv/bin
    # /www/server/panel/pyenv/bin/pip install cachelib
    /www/server/panel/pyenv/bin/pip install python-telegram-bot==20.3
    password=$(cat /dev/urandom | head -n 16 | md5sum | head -c 8)
    if [ "$PANEL_PASSWORD" ];then
        password=$PANEL_PASSWORD
    fi
    sleep 1
    admin_auth="/www/server/panel/data/admin_path.pl"
    if [ ! -f ${admin_auth} ]; then
        auth_path=$(cat /dev/urandom | head -n 16 | md5sum | head -c 8)
        echo "/${auth_path}" >${admin_auth}
    fi
    if [ "${SAFE_PATH}" ];then
        auth_path=$SAFE_PATH
        echo "/${auth_path}" > ${admin_auth}
    fi
    auth_path=$(cat ${admin_auth})
    # /www/server/panel/pyenv/bin/pip3 install pymongo
    # /www/server/panel/pyenv/bin/pip3 install psycopg2-binary
    # /www/server/panel/pyenv/bin/pip3 install flask -U
    # /www/server/panel/pyenv/bin/pip3 install flask-sock
    # /www/server/panel/pyenv/bin/pip3 install simple-websocket==0.10.0
    check_pyOpenSSL=$(/www/server/panel/pyenv/bin/pip list|grep pyOpenSSL)
    if [ -z "$check_pyOpenSSL" ]; then
        /www/server/panel/pyenv/bin/pip install -I pyOpenSSl
    fi
    cd ${setup_path}/server/panel/
    if [ "$SET_SSL" == true ]; then
        # mkdir /www/server/panel/ssl
        echo "SET ssl, please wait...."
        ssl=$(/www/server/panel/pyenv/bin/python /www/server/panel/tools.py ssl)
        echo ${ssl}
        if [[ "${ssl}" -eq 1 ]];then
            if [ -s "/www/server/panel/ssl/certificate.pem" ];then
                check_certificate=$(openssl x509 -noout -modulus -in /www/server/panel/ssl/certificate.pem | openssl md5)
                check_privateKey=$(openssl rsa -noout -modulus -in /www/server/panel/ssl/privateKey.pem | openssl md5)
                if [ "${check_certificate}" != "${check_privateKey}" ];then
                    echo -e "The certificate and privateKey are not consistent, Use the built-in SSL certificate."
                    Use_self_signed_certificate
                fi
            else
                Use_self_signed_certificate
            fi
        else
            Use_self_signed_certificate
        fi
        echo "SET_SSL: $SET_SSL"
    fi
    /etc/init.d/bt start
    # sleep 5
    $python_bin -m py_compile tools.py
    $python_bin tools.py username
    username=$($python_bin tools.py panel ${password})
    if [ "$PANEL_USER" ];then
        username=$PANEL_USER
    fi
    cd ~
    echo "${password}" >${setup_path}/server/panel/default.pl
    chmod 600 ${setup_path}/server/panel/default.pl
    sleep 3
    /etc/init.d/bt restart
    sleep 5
    isStart=$(ps aux | grep 'BT-Panel' | grep -v grep | awk '{print $2}')
    if [ -z "${isStart}" ]; then
        /etc/init.d/bt start
        sleep 5
        isStart=$(ps aux | grep 'BT-Panel' | grep -v grep | awk '{print $2}')
        if [ -z "${isStart}" ]; then
            Check_PIP_Packages
            /etc/init.d/bt start
            sleep 5
            isStart=$(ps aux | grep 'BT-Panel' | grep -v grep | awk '{print $2}')
        fi
    fi

    LOCAL_CURL=$(curl 127.0.0.1:$panelPort/login 2>&1 | grep -i html)
    if [ -z "${isStart}" ] && [ -z "${LOCAL_CURL}" ]; then
        /etc/init.d/bt 22
        cd /www/server/panel/pyenv/bin
        touch t.pl
        ls -al python3.12 python3 python ${setup_path}/server/panel/BT-*
        lsattr python3.12 python3 python
        Red_Error "ERROR: The BT-Panel service startup failed."
    fi

    if [ "$PANEL_USER" ];then
        cd ${setup_path}/server/panel/
        btpython -c 'import tools;tools.set_panel_username("'$PANEL_USER'")'
        cd ~
    fi
    if [ -f "/usr/bin/sqlite3" ] ;then
        #sqlite3 /www/server/panel/data/db/panel.db "UPDATE config SET status = '1' WHERE id = '1';"  > /dev/null 2>&1
        sqlite3 /www/server/panel/data/default.db "UPDATE config SET status = '1' WHERE id = '1';"  > /dev/null 2>&1
    fi

    touch /www/server/panel/install/i_mysql.pl
    
}
Set_Firewall() {
    sshPort=$(cat /etc/ssh/sshd_config | grep 'Port ' | awk '{print $2}')
    if [ "${PM}" = "apt-get" ]; then
        if [ ! -f "/usr/bin/ufw" ] && [ ! -f "/bin/ufw" ] && ! Command_Exists "ufw"; then
            apt-get install -y ufw
        fi
        if [ -f "/usr/sbin/ufw" ]; then
            ufw allow 20/tcp >/dev/null 2>&1
            ufw allow 21/tcp >/dev/null 2>&1
            ufw allow 22/tcp >/dev/null 2>&1
            ufw allow 80/tcp >/dev/null 2>&1
            ufw allow 443/tcp >/dev/null 2>&1
            ufw allow 888/tcp >/dev/null 2>&1
            ufw allow 39000:40000/tcp >/dev/null 2>&1
            ufw allow ${panelPort}/tcp >/dev/null 2>&1
            ufw allow ${sshPort}/tcp >/dev/null 2>&1
            ufw_status=$(ufw status)
            echo y | ufw enable
            ufw default deny
            ufw reload
        fi
    else
        if [ -f "/etc/init.d/iptables" ]; then
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 20 -j ACCEPT
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 21 -j ACCEPT
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 80 -j ACCEPT
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 443 -j ACCEPT
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport ${panelPort} -j ACCEPT
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport ${sshPort} -j ACCEPT
            iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport 39000:40000 -j ACCEPT
            #iptables -I INPUT -p tcp -m state --state NEW -m udp --dport 39000:40000 -j ACCEPT
            iptables -A INPUT -p icmp --icmp-type any -j ACCEPT
            iptables -A INPUT -s localhost -d localhost -j ACCEPT
            iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
            iptables -P INPUT DROP
            service iptables save
            sed -i "s#IPTABLES_MODULES=\"\"#IPTABLES_MODULES=\"ip_conntrack_netbios_ns ip_conntrack_ftp ip_nat_ftp\"#" /etc/sysconfig/iptables-config
            iptables_status=$(service iptables status | grep 'not running')
            if [ "${iptables_status}" == '' ]; then
                service iptables restart
            fi
        else
            AliyunCheck=$(cat /etc/redhat-release | grep "Aliyun Linux")
            [ "${AliyunCheck}" ] && return
            if [ ! -f "/usr/bin/firewall-cmd" ] && [ ! -f "/bin/firewall-cmd" ] && ! Command_Exists "firewall-cmd"; then
                yum install firewalld -y
            fi
            [ "${Centos8Check}" ] && yum reinstall python3-six -y
            systemctl enable firewalld
            systemctl start firewalld
            firewall-cmd --set-default-zone=public >/dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=20/tcp >/dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=21/tcp >/dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=22/tcp >/dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=80/tcp >/dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=443/tcp > /dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=${panelPort}/tcp >/dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=${sshPort}/tcp >/dev/null 2>&1
            firewall-cmd --permanent --zone=public --add-port=39000-40000/tcp >/dev/null 2>&1
            #firewall-cmd --permanent --zone=public --add-port=39000-40000/udp > /dev/null 2>&1
            firewall-cmd --reload
        fi
    fi
}
Get_Ip_Address() {
    getIpAddress=""
    # 	getIpAddress=$(curl -sS --connect-timeout 10 -m 60 https://brandnew.aapanel.com/api/common/getClientIP)
    # getIpAddress=$(curl -sSk --connect-timeout 10 -m 60 https://www.aapanel.com/api/common/getClientIP)


    ipv4_address=""
    ipv6_address=""
    ipv4_address=$(curl -4 -sS --connect-timeout 10 -m 15 https://www.aapanel.com/api/common/getClientIP 2>&1)
    if [ -z "${ipv4_address}" ];then
            ipv4_address=$(curl -4 -sS --connect-timeout 10 -m 15 https://ifconfig.me 2>&1)
            if [ -z "${ipv4_address}" ];then
                ipv4_address=$(curl -4 -sS --connect-timeout 10 -m 15 https://www.bt.cn/Api/getIpAddress 2>&1)
            fi
    fi
    IPV4_REGEX="^([0-9]{1,3}\.){3}[0-9]{1,3}$"
    if ! [[ $ipv4_address =~ $IPV4_REGEX ]]; then
            ipv4_address=""
    fi
    
    ipv6_address=$(curl -6 -sS --connect-timeout 10 -m 15 https://www.aapanel.com/api/common/getClientIP 2>&1)
    # IPV6_REGEX="^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    IPV6_REGEX="^([0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4}$"
    if ! [[ $ipv6_address =~ $IPV6_REGEX ]]; then
            ipv6_address=""
    else
        if [[ ! $ipv6_address =~ ^\[ ]]; then
            ipv6_address="[$ipv6_address]"
        fi
    fi

    if [ "${ipv4_address}" ];then
        getIpAddress=$ipv4_address
    elif [ "${ipv6_address}" ];then
        getIpAddress=$ipv6_address
    fi


    ipv4Check=$($python_bin -c "import re; print(re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$','${getIpAddress}'))")
    if [ "${ipv4Check}" == "None" ]; then
        ipv6Address=$(echo ${getIpAddress} | tr -d "[]")
        ipv6Check=$($python_bin -c "import re; print(re.match(r'^([0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4}$','${ipv6Address}'))")
        if [ "${ipv6Check}" == "None" ]; then
            getIpAddress="SERVER_IP"
        else
            getIpAddress=$(echo "[$getIpAddress]")
            echo "True" >${setup_path}/server/panel/data/ipv6.pl
            sleep 1
            # /etc/init.d/bt restart
        fi
    fi

    if [ "${getIpAddress}" != "SERVER_IP" ]; then
        echo "${getIpAddress}" >${setup_path}/server/panel/data/iplist.txt
    fi
}
Setup_Count() {
    curl -sSk --connect-timeout 10 -m 60 https://www.aapanel.com/api/setupCount/setupPanel?o=$1 >/dev/null 2>&1
    # curl -sS --connect-timeout 10 -m 60 https://console.aapanel.com/Api/SetupCount?type=Linux > /dev/null 2>&1
    if [ "$1" != "" ]; then
        echo $1 >/www/server/panel/data/o.pl
        cd /www/server/panel
        $python_bin tools.py o
    fi
    echo /www >/var/bt_setupPath.conf
}

Install_Main() {

    Check_Disk_Space
    startTime=$(date +%s)
    Lock_Clear
    System_Check
    Set_Ssl
    Get_Pack_Manager
    get_node_url

    MEM_TOTAL=$(free -g | grep Mem | awk '{print $2}')
    if [ "${MEM_TOTAL}" -le "1" ]; then
        Auto_Swap
    fi

    if [ "${PM}" = "yum" ]; then
        Install_RPM_Pack
    elif [ "${PM}" = "apt-get" ]; then
        Install_Deb_Pack
    fi

    Check_Install_Sys_Packs

    Install_Python_Lib
    Install_Bt

    Set_Bt_Panel
    Service_Add
    Set_Firewall

    Get_Ip_Address
    Setup_Count ${IDC_CODE}
}

echo "
+----------------------------------------------------------------------
| aaPanel FOR CentOS/Ubuntu/Debian
+----------------------------------------------------------------------
| Copyright © 2015-2099 BT-SOFT(https://www.aapanel.com) All rights reserved.
+----------------------------------------------------------------------
| The WebPanel URL will be https://SERVER_IP:$panelPort when installed.
+----------------------------------------------------------------------
"

while [ ${#} -gt 0 ]; do
    case $1 in
        -h|--help)
            echo "Usage:  [options]"
            echo "Options:"
            echo "  -u, --user                  Set aaPanel user name"
            echo "  -p, --password              Set aaPanel password"
            echo "  -P, --port                  Set aaPanel port"
            echo "  --safe-path                 Set aaPanel safe path"
            exit 0
            ;;
        -u|--user)
            PANEL_USER=$2
            shift 1
            ;;
        -p|--password)
            PANEL_PASSWORD=$2
            shift 1
            ;;
        -P|--port)
            PANEL_PORT=$2
            shift 1
            ;;
        --safe-path)
            SAFE_PATH=$2
            shift 1
            ;;
        --ssl-disable)
            SSL_PL="disable"
            ;;
        -y)
            go="y"
            ;;
        *)
            IDC_CODE=$1
            ;;
    esac
    shift 1
done
while [ "$go" != 'y' ] && [ "$go" != 'n' ]; do
    read -p "Do you want to install aaPanel to the $setup_path directory now?(y/n): " go
done

if [ "$go" == 'n' ]; then
    exit
fi

Install_Main
/etc/init.d/bt restart
intenal_ip=$(ip addr | grep -E -o '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | grep -E -v "^127\.|^255\.|^0\." | head -n 1)
echo -e "=================================================================="
echo -e "\033[32mCongratulations! Installed successfully!\033[0m"
echo -e "=================================================================="
if [[ "$SET_SSL" == "true" ]]; then
    HTTP_S="https"
else
    HTTP_S="http"
fi
echo "aaPanel Internet Address: ${HTTP_S}://${getIpAddress}:${panelPort}$auth_path"
echo "aaPanel Internal Address: ${HTTP_S}://${intenal_ip}:${panelPort}$auth_path"
echo -e "username: $username"
echo -e "password: $password"
echo -e "\033[33mWarning:\033[0m"
echo -e "\033[33mIf you cannot access the panel, \033[0m"
echo -e "\033[33mrelease the following port ($panelPort|888|80|443|20|21) in the security group\033[0m"
echo -e "=================================================================="

endTime=$(date +%s)
((outTime = ($endTime - $startTime) / 60))
if [ "${outTime}" == "0" ];then
    ((outTime=($endTime-$startTime)))
    echo -e "Time consumed:\033[32m $outTime \033[0mseconds!"
else
    echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"
fi
rm -f install_7.0_en.sh /tmp/pip_en_3.12.txt ${check_pip_packs} ${show_pip_list_panel}

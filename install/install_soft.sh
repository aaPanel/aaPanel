#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

serverUrl=https://node.aapanel.com/install
mtype=$1
actionType=$2
name=$3
version=$4

check_dash=$(readlink -f /bin/sh)
if [ "$check_dash" = "/usr/bin/dash" ] || [ "$check_dash" = "/bin/dash" ] || [ "$check_dash" = "dash" ]; then
    if [ -f "/usr/bin/bash" ]; then
        ln -sf /usr/bin/bash /bin/sh
    elif [ -f "/bin/bash" ]; then
        ln -sf /bin/bash /bin/sh
    fi
fi


if [ ! -f 'lib.sh' ];then
	wget -O lib.sh $serverUrl/$mtype/lib.sh --no-check-certificate
fi

libNull=`cat lib.sh`
if [ "$libNull" == '' ];then
	wget --no-check-certificate -O lib.sh $serverUrl/$mtype/lib.sh
fi

wget --no-check-certificate -O $name.sh $serverUrl/$mtype/$name.sh
if [ "$actionType" == 'install' ];then
	bash lib.sh
fi

sed -i 's/download\.bt\.cn/node\.aapanel\.com/g' $name.sh

bash $name.sh $actionType $version

echo '|-Successify --- Command executed! ---'

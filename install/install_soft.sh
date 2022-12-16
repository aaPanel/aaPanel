#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

#CN='125.88.182.172'
#HK='download.bt.cn'
#HK2='103.224.251.67'
#US='128.1.164.196'
#sleep 0.5;
#CN_PING=`ping -c 1 -w 1 $CN|grep time=|awk '{print $7}'|sed "s/time=//"`
#HK_PING=`ping -c 1 -w 1 $HK|grep time=|awk '{print $7}'|sed "s/time=//"`
#HK2_PING=`ping -c 1 -w 1 $HK2|grep time=|awk '{print $7}'|sed "s/time=//"`
#US_PING=`ping -c 1 -w 1 $US|grep time=|awk '{print $7}'|sed "s/time=//"`

#echo "$HK_PING $HK" > ping.pl
#echo "$HK2_PING $HK2" >> ping.pl
#echo "$US_PING $US" >> ping.pl
#echo "$CN_PING $CN" >> ping.pl
nodeAddr=`sort -V ping.pl|sed -n '1p'|awk '{print $2}'`
#if [ "$nodeAddr" == "" ];then
#	nodeAddr=$HK2
#fi
#serverUrl=http://$nodeAddr:5880/install
serverUrl=https://node.aapanel.com/install
mtype=$1
actionType=$2
name=$3
version=$4

if [ ! -f 'lib.sh' ];then
	wget -O lib.sh $serverUrl/$mtype/lib.sh --no-check-certificate
fi
wget -O $name.sh $serverUrl/$mtype/$name.sh --no-check-certificate
if [ "$actionType" == 'install' ];then
	sh lib.sh
fi
sh $name.sh $actionType $version

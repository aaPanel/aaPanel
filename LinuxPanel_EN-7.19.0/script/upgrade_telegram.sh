#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
echo 'skip telegram'
#
#is_flask1=$(/www/server/panel/pyenv/bin/pip3 list|grep 'telegram'|grep '0.0.1')
#if [ "${is_flask1}" != "" ];then
#   echo "Y" | /www/server/panel/pyenv/bin/pip3 uninstall telegram
#fi
#
#is_flask2=$(/www/server/panel/pyenv/bin/pip3 list|grep 'python-telegram-bot'|grep '20.3' )
#if [ "${is_flask2}" = "" ];then
#   /www/server/panel/pyenv/bin/pip3 install python-telegram-bot==20.3 -I
#else
#  exit;
#fi
#
#rm -f /www/server/panel/script/upgrade_telegram.sh
#bash /www/server/panel/init.sh reload

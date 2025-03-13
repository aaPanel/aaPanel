#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

    mypip="/www/server/panel/pyenv/bin/pip3"
    pyroute2_path="/www/server/panel/script/pyroute2-0.7.12-py3-none-any.whl"

    change_pip_package_list=$( $mypip list | grep -E "pyroute2" )
    
    pyroute2_v=$(echo "$change_pip_package_list" | grep pyroute2)
    if [ "$pyroute2_v" = "" ];then
        echo "Update pyroute2"
        $mypip install $pyroute2_path
        rm -f $pyroute2_path

        pyroute2_v_2=$($mypip list |grep pyroute2)
        if [ "$pyroute2_v_2" = "" ];then
            $mypip install pyroute2
        fi
    fi
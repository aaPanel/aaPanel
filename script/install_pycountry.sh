#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

    mypip="/www/server/panel/pyenv/bin/pip3"
    pycountry_path="/www/server/panel/script/pycountry-24.6.1-py3-none-any.whl"

    change_pip_package_list=$( $mypip list | grep -E "pycountry" )
    
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
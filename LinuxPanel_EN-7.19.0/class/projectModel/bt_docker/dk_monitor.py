#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: zouhw <zhw@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# Docker模型
#------------------------------
import sys #line:1
import threading #line:2
sys .path .insert (0 ,"/www/server/panel/class/")#line:3
sys .path .insert (1 ,"/www/server/panel/")#line:4
import projectModel .bt_docker .dk_public as dp #line:5
import projectModel .bt_docker .dk_container as dc #line:6
import projectModel .bt_docker .dk_status as ds #line:7
import projectModel .bt_docker .dk_image as di #line:8
import public #line:9
import time #line:11
class main :#line:12
    __OOOOO0OOO0OO00O00 =None #line:14
    __OOOOOO0OO0OOOOOO0 =86400 #line:15
    def __init__ (O00O000000O0OO0OO ,OO00OO00O0O00OO0O ):#line:17
        if not OO00OO00O0O00OO0O :#line:18
            O00O000000O0OO0OO .__OOOOO0OOO0OO00O00 =30 #line:19
        else :#line:20
            O00O000000O0OO0OO .__OOOOO0OOO0OO00O00 =OO00OO00O0O00OO0O #line:21
    def docker_client (OOOOO000OO0O00OO0 ,OO00OOO0000OO0000 ):#line:23
        return dp .docker_client (OO00OOO0000OO0000 )#line:24
    def get_all_host_stats (O0000O0000OO0O000 ,O000O0O00OO00O00O ):#line:26
        ""#line:31
        OO000O0OO0O0O0000 =dp .sql ('hosts').select ()#line:32
        for O00O0OO00O0O000O0 in OO000O0OO0O0O0000 :#line:33
            O0OO00O0O00O0000O =threading .Thread (target =O000O0O00OO00O00O ,args =(O00O0OO00O0O000O0 ,))#line:34
            O0OO00O0O00O0000O .setDaemon (True )#line:35
            O0OO00O0O00O0000O .start ()#line:36
    def container_status_for_all_hosts (OO0O00OO0O0OOOO0O ,OOOOOOO000OO0OOO0 ):#line:39
        ""#line:44
        O000OO000O0O00O00 =public .to_dict_obj ({})#line:46
        O000OO000O0O00O00 .url =OOOOOOO000OO0OOO0 ['url']#line:47
        O0O0O0O000O00O0OO =dc .main ().get_list (O000OO000O0O00O00 )['msg']#line:48
        for O00OOOOOOOO00OOO0 in O0O0O0O000O00O0OO ['container_list']:#line:49
            O000OO000O0O00O00 .id =O00OOOOOOOO00OOO0 ['id']#line:50
            O000OO000O0O00O00 .write =1 #line:51
            O000OO000O0O00O00 .save_date =OO0O00OO0O0OOOO0O .__OOOOO0OOO0OO00O00 #line:52
            ds .main ().stats (O000OO000O0O00O00 )#line:53
    def container_count (OO0000O0O0O0OOO00 ):#line:57
        O0O000O0O000O000O =dp .sql ('hosts').select ()#line:59
        O0O00O00O0O00OOO0 =0 #line:60
        for O0O0O00OO0OO0O0O0 in O0O000O0O000O000O :#line:61
            O00OOOO00OO0OOO00 =public .to_dict_obj ({})#line:62
            O00OOOO00OO0OOO00 .url =O0O0O00OO0OO0O0O0 ['url']#line:63
            OO00OO00O0O00O00O =dc .main ().get_list (O00OOOO00OO0OOO00 )['msg']#line:64
            O0O00O00O0O00OOO0 +=len (OO00OO00O0O00O00O )#line:65
        O0000000000000000 ={"time":int (time .time ()),"container_count":O0O00O00O0O00OOO0 }#line:69
        OOOOO0OO00OOO0O0O =time .time ()-(OO0000O0O0O0OOO00 .__OOOOO0OOO0OO00O00 *OO0000O0O0O0OOO00 .__OOOOOO0OO0OOOOOO0 )#line:70
        dp .sql ("container_count").where ("time<?",(OOOOO0OO00OOO0O0O ,)).delete ()#line:71
        dp .sql ("container_count").insert (O0000000000000000 )#line:72
    def image_for_all_host (OO0O00O000OO00O0O ):#line:75
        OO000OO0OOO00OO0O =dp .sql ('hosts').select ()#line:77
        OOO0OOO00O000OOOO =0 #line:78
        O0O00000OO0O0O000 =0 #line:79
        for O00OOO00O0000O00O in OO000OO0OOO00OO0O :#line:80
            O0O00O0OOOO0O00O0 =public .to_dict_obj ({})#line:81
            O0O00O0OOOO0O00O0 .url =O00OOO00O0000O00O ['url']#line:82
            OO00O0000O0000O00 =di .main ().image_for_host (O0O00O0OOOO0O00O0 )#line:83
            if not OO00O0000O0000O00 ['status']:#line:84
                continue #line:85
            print (OO00O0000O0000O00 )#line:86
            OOO0OOO00O000OOOO +=OO00O0000O0000O00 ['msg']['num']#line:87
            O0O00000OO0O0O000 +=OO00O0000O0000O00 ['msg']['size']#line:88
        O0OO0O00O000000OO ={"time":int (time .time ()),"num":OOO0OOO00O000OOOO ,"size":int (O0O00000OO0O0O000 )}#line:93
        O0O000O00OO0OO0O0 =time .time ()-(OO0O00O000OO00O0O .__OOOOO0OOO0OO00O00 *OO0O00O000OO00O0O .__OOOOOO0OO0OOOOOO0 )#line:94
        dp .sql ("image_infos").where ("time<?",(O0O000O00OO0OO0O0 ,)).delete ()#line:95
        dp .sql ("image_infos").insert (O0OO0O00O000000OO )#line:96
def monitor ():#line:99
    while True :#line:102
        O0OOO000OOO0OOO00 =dp .docker_conf ()['SAVE']#line:103
        O000OO0O0O0OO0000 =main (O0OOO000OOO0OOO00 )#line:104
        O000OO0O0O0OO0000 .get_all_host_stats (O000OO0O0O0OO0000 .container_status_for_all_hosts )#line:105
        O0000OO0000000O00 =threading .Thread (target =O000OO0O0O0OO0000 .container_count )#line:107
        O0000OO0000000O00 .setDaemon (True )#line:108
        O0000OO0000000O00 .start ()#line:109
        O0000OO0000000O00 =threading .Thread (target =O000OO0O0O0OO0000 .image_for_all_host )#line:111
        O0000OO0000000O00 .setDaemon (True )#line:112
        O0000OO0000000O00 .start ()#line:113
        time .sleep (60 )#line:114
if __name__ =="__main__":#line:119
    monitor ()
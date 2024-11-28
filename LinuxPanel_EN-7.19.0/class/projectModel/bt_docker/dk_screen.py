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
import projectModel.bt_docker.dk_public as dp
import time

class main :#line:1
    def get_status (O00OO00O00O0OO00O ,OOO0000O00O0OOO0O ):#line:3
        ""#line:9
        O000OO00O0O0OOO0O =dict ()#line:10
        O000OO00O0O0OOO0O ['container_count']=O00OO00O00O0OO00O .__O0OO000000O0OO0O0 (OOO0000O00O0OOO0O )#line:12
        O000OO00O0O0OOO0O ['image_info']=dp .sql ("image_infos").where ("time>=? and time<=?",(OOO0000O00O0OOO0O .start_time ,OOO0000O00O0OOO0O .stop_time )).select ()#line:14
        O000OO00O0O0OOO0O ['host']=len (dp .sql ('hosts').select ())#line:16
        O000OO00O0O0OOO0O ['container_top']={"cpu":O00OO00O00O0OO00O .__OO0OOO00O0OOO0OOO (),"mem":O00OO00O00O0OO00O .__O0OO00OOO00O00OOO ()}#line:18
        return O000OO00O0O0OOO0O #line:19
    def __O0OO000000O0OO0O0 (OOOO0OO0O00O0OOOO ,OO0OO0OO000O00O0O ):#line:21
        O0OOO000O0OOOO0O0 =dp .sql ('container_count').where ("time>=? and time<=?",(OO0OO0OO000O00O0O .start_time ,OO0OO0OO000O00O0O .stop_time )).select ()#line:22
        if not O0OOO000O0OOOO0O0 :#line:23
            return 0 #line:24
        return O0OOO000O0OOOO0O0 [-1 ]#line:25
    def __O0OO00OOO00O00OOO (OOO0OOO0O00OOOOO0 ):#line:27
        O000OO0O00O0O00OO =int (time .time ())#line:28
        O0OO0O0OO0O00O0O0 =O000OO0O00O0O00OO -3600 #line:29
        OO0O000OO00OO0OOO =dp .sql ("mem_stats").where ("time>=? and time<=?",(O0OO0O0OO0O00O0O0 ,O000OO0O00O0O00OO )).select ()#line:30
        O000O0OO00OOOO0O0 =list ()#line:31
        O0O0O000OO00OOOOO =dict ()#line:32
        for O00OOOO0OOOO00000 in OO0O000OO00OO0OOO :#line:34
            O000O0OO00OOOO0O0 .append (O00OOOO0OOOO00000 ['container_id'])#line:35
        O000O0OO00OOOO0O0 =set (O000O0OO00OOOO0O0 )#line:37
        for OO0O0OO000OO0OO00 in O000O0OO00OOOO0O0 :#line:38
            OO0000OOOOOOOO000 =0 #line:39
            OO0000O00O000000O =0 #line:40
            for O00OOOO0OOOO00000 in OO0O000OO00OO0OOO :#line:41
                if O00OOOO0OOOO00000 ['container_id']==OO0O0OO000OO0OO00 :#line:42
                    OO0000OOOOOOOO000 +=1 #line:43
                    OO0000O00O000000O +=float (O00OOOO0OOOO00000 ['usage'])#line:44
            if OO0000OOOOOOOO000 !=0 :#line:45
                O0O0O000OO00OOOOO [OO0O0OO000OO0OO00 ]=OO0000O00O000000O /OO0000OOOOOOOO000 #line:46
        return O0O0O000OO00OOOOO #line:47
    def __OO0OOO00O0OOO0OOO (O0O0O0O000OOO000O ):#line:49
        O0O0OO0OO00OO0000 =int (time .time ())#line:50
        OO000OOO00OO0OOO0 =O0O0OO0OO00OO0000 -3600 #line:51
        OO000O0OOOO0OO00O =dp .sql ("cpu_stats").where ("time>=? and time<=?",(OO000OOO00OO0OOO0 ,O0O0OO0OO00OO0000 )).select ()#line:52
        OOO00O00O0OO0O0OO =list ()#line:53
        OO0OOOOOO000OO000 =dict ()#line:54
        for O0000O0O0000O0OOO in OO000O0OOOO0OO00O :#line:56
            OOO00O00O0OO0O0OO .append (O0000O0O0000O0OOO ['container_id'])#line:57
        OOO00O00O0OO0O0OO =set (OOO00O00O0OO0O0OO )#line:59
        for OO0OO00OOOOOO0O0O in OOO00O00O0OO0O0OO :#line:60
            OO00O0000000OO0OO =0 #line:61
            OO0OOOO0OOOO000O0 =0 #line:62
            for O0000O0O0000O0OOO in OO000O0OOOO0OO00O :#line:63
                if O0000O0O0000O0OOO ['container_id']==OO0OO00OOOOOO0O0O :#line:64
                    OO00O0000000OO0OO +=1 #line:65
                    OO0OOOO0OOOO000O0 +=float (0 if O0000O0O0000O0OOO ['cpu_usage']=='0.0'else O0000O0O0000O0OOO ['cpu_usage'])#line:66
            if OO00O0000000OO0OO !=0 :#line:67
                OO0OOOOOO000OO000 [OO0OO00OOOOOO0O0O ]=OO0OOOO0OOOO000O0 /OO00O0000000OO0OO #line:68
        return OO0OOOOOO000OO000
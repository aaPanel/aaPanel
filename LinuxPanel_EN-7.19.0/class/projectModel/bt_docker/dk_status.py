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
import public #line:13
import time #line:14
import projectModel .bt_docker .dk_public as dp #line:15
class main :#line:18
    __OOOO00OOO0O00O0O0 =dict ()#line:20
    __OO0O0O00OO0OOO000 =None #line:21
    def docker_client (OOOOOO000OOOO0OOO ,OO0OOO0O0O00O0000 ):#line:23
        if not OOOOOO000OOOO0OOO .__OO0O0O00OO0OOO000 :#line:24
            OOOOOO000OOOO0OOO .__OO0O0O00OO0OOO000 =dp .docker_client (OO0OOO0O0O00O0000 )#line:25
        return OOOOOO000OOOO0OOO .__OO0O0O00OO0OOO000 #line:26
    def io_stats (O00OOOOO000OO00OO ,O00O0OO0000OO0O0O ,write =None ):#line:28
        O0O0OO0OOO0OO0000 =O00O0OO0000OO0O0O ['blkio_stats']['io_service_bytes_recursive']#line:29
        if len (O0O0OO0OOO0OO0000 )<=2 :#line:30
            try :#line:31
                O0OO0OO0O000OOOOO =O0O0OO0OOO0OO0000 [0 ]['value']#line:32
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['read_total']=O0OO0OO0O000OOOOO #line:33
            except :#line:34
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['read_total']=0 #line:35
            try :#line:36
                O0OO0OO0O000OOOOO =O0O0OO0OOO0OO0000 [1 ]['value']#line:37
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['write_total']=O0OO0OO0O000OOOOO #line:38
            except :#line:39
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['write_total']=0 #line:40
        else :#line:41
            try :#line:42
                O0OO0OO0O000OOOOO =O0O0OO0OOO0OO0000 [0 ]['value']+O0O0OO0OOO0OO0000 [2 ]['value']#line:43
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['read_total']=O0OO0OO0O000OOOOO #line:44
            except :#line:45
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['read_total']=0 #line:46
            try :#line:47
                O0OO0OO0O000OOOOO =O0O0OO0OOO0OO0000 [1 ]['value']+O0O0OO0OOO0OO0000 [3 ]['value']#line:48
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['write_total']=O0OO0OO0O000OOOOO #line:49
            except :#line:50
                O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['write_total']=0 #line:51
        if write :#line:52
            O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 ['container_id']=O00O0OO0000OO0O0O ['id']#line:53
            O00OOOOO000OO00OO .write_io (O00OOOOO000OO00OO .__OOOO00OOO0O00O0O0 )#line:54
    def net_stats (OOO0000O0O0O00O0O ,O0O0OOO00O0000OOO ,OO0O0O000OOO000OO ,write =None ):#line:56
        try :#line:57
            OO00OOOO0O0000OOO =O0O0OOO00O0000OOO ['networks']['eth0']#line:58
            OOO00O00O0O00OOOO =OO0O0O000OOO000OO ['networks']['eth0']#line:59
        except :#line:60
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['rx_total']=0 #line:61
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['rx']=0 #line:62
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['tx_total']=0 #line:63
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['tx']=0 #line:64
            if write :#line:65
                OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['container_id']=O0O0OOO00O0000OOO ['id']#line:66
                OOO0000O0O0O00O0O .write_net (OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 )#line:67
            return #line:68
        O0000OO00OO0OOO00 =O0O0OOO00O0000OOO ["time"]#line:69
        O0000OO0OO0OOOOOO =OO0O0O000OOO000OO ["time"]#line:70
        try :#line:71
            O0O000O00O0OO0OO0 =OO00OOOO0O0000OOO ["rx_bytes"]#line:72
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['rx_total']=O0O000O00O0OO0OO0 #line:73
            O0000OOO0OO00OOO0 =OOO00O00O0O00OOOO ["rx_bytes"]#line:74
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['rx']=int ((O0O000O00O0OO0OO0 -O0000OOO0OO00OOO0 )/(O0000OO00OO0OOO00 -O0000OO0OO0OOOOOO ))#line:75
        except :#line:76
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['rx_total']=0 #line:77
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['rx']=0 #line:78
        try :#line:79
            O0O000O00O0OO0OO0 =OO00OOOO0O0000OOO ["tx_bytes"]#line:80
            O0000OOO0OO00OOO0 =OOO00O00O0O00OOOO ["tx_bytes"]#line:81
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['tx_total']=O0O000O00O0OO0OO0 #line:82
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['tx']=int ((O0O000O00O0OO0OO0 -O0000OOO0OO00OOO0 )/(O0000OO00OO0OOO00 -O0000OO0OO0OOOOOO ))#line:83
        except :#line:84
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['tx_total']=0 #line:85
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['tx']=0 #line:86
        if write :#line:87
            OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 ['container_id']=O0O0OOO00O0000OOO ['id']#line:88
            OOO0000O0O0O00O0O .write_net (OOO0000O0O0O00O0O .__OOOO00OOO0O00O0O0 )#line:89
    def mem_stats (O0OO000OOO0O0O000 ,O00OOO0OO00OOO000 ,write =None ):#line:92
        OOO0000OO0OOO000O =O00OOO0OO00OOO000 ['memory_stats']#line:93
        try :#line:94
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['limit']=OOO0000OO0OOO000O ['limit']#line:95
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['usage_total']=OOO0000OO0OOO000O ['usage']#line:96
            if 'cache'not in OOO0000OO0OOO000O ['stats']:#line:97
                OOO0000OO0OOO000O ['stats']['cache']=0 #line:98
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['usage']=OOO0000OO0OOO000O ['usage']-OOO0000OO0OOO000O ['stats']['cache']#line:99
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['cache']=OOO0000OO0OOO000O ['stats']['cache']#line:100
        except :#line:102
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['limit']=0 #line:104
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['usage']=0 #line:105
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['cache']=0 #line:106
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['usage_total']=0 #line:107
        if write :#line:109
            O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 ['container_id']=O00OOO0OO00OOO000 ['id']#line:110
            O0OO000OOO0O0O000 .write_mem (O0OO000OOO0O0O000 .__OOOO00OOO0O00O0O0 )#line:111
    def cpu_stats (OO0OO000OO000O000 ,OO0000OOO00OO0O0O ,write =None ):#line:114
        try :#line:120
            OOOOO0O0OO0O00O0O =OO0000OOO00OO0O0O ['cpu_stats']['cpu_usage']['total_usage']-OO0000OOO00OO0O0O ['precpu_stats']['cpu_usage']['total_usage']#line:121
        except :#line:122
            OOOOO0O0OO0O00O0O =0 #line:123
        try :#line:124
            OO00000O0O0OO0O00 =OO0000OOO00OO0O0O ['cpu_stats']['system_cpu_usage']-OO0000OOO00OO0O0O ['precpu_stats']['system_cpu_usage']#line:125
        except :#line:126
            OO00000O0O0OO0O00 =0 #line:127
        try :#line:128
            OO0OO000OO000O000 .__OOOO00OOO0O00O0O0 ['online_cpus']=OO0000OOO00OO0O0O ['cpu_stats']['online_cpus']#line:129
        except :#line:130
            OO0OO000OO000O000 .__OOOO00OOO0O00O0O0 ['online_cpus']=0 #line:131
        if OOOOO0O0OO0O00O0O >0 and OO00000O0O0OO0O00 >0 :#line:132
            OO0OO000OO000O000 .__OOOO00OOO0O00O0O0 ['cpu_usage']=round ((OOOOO0O0OO0O00O0O /OO00000O0O0OO0O00 )*100 *OO0OO000OO000O000 .__OOOO00OOO0O00O0O0 ['online_cpus'],2 )#line:133
        else :#line:134
            OO0OO000OO000O000 .__OOOO00OOO0O00O0O0 ['cpu_usage']=0.0 #line:135
        if write :#line:136
            OO0OO000OO000O000 .__OOOO00OOO0O00O0O0 ['container_id']=OO0000OOO00OO0O0O ['id']#line:137
            OO0OO000OO000O000 .write_cpu (OO0OO000OO000O000 .__OOOO00OOO0O00O0O0 )#line:138
    def stats (OO0OOOO00OO0OO000 ,OO00OO0OO00OOO0O0 ):#line:141
        ""#line:148
        OOOOO00O00000OOO0 =OO0OOOO00OO0OO000 .docker_client (OO00OO0OO00OOO0O0 .url ).containers .get (OO00OO0OO00OOO0O0 .id )#line:149
        O00O0OOOO000O0O0O =OOOOO00O00000OOO0 .stats (decode =None ,stream =False )#line:150
        O00O0OOOO000O0O0O ['time']=time .time ()#line:151
        OOOOOOOOO0OO0O00O =public .cache_get ('stats')#line:152
        if not OOOOOOOOO0OO0O00O :#line:153
            OOOOOOOOO0OO0O00O =O00O0OOOO000O0O0O #line:154
            public .cache_set ('stats',O00O0OOOO000O0O0O )#line:155
        OOO000O0000O0OO0O =None #line:156
        if hasattr (OO00OO0OO00OOO0O0 ,"write"):#line:157
            OOO000O0000O0OO0O =OO00OO0OO00OOO0O0 .write #line:158
            OO0OOOO00OO0OO000 .__OOOO00OOO0O00O0O0 ['expired']=time .time ()-(OO00OO0OO00OOO0O0 .save_date *86400 )#line:159
        O00O0OOOO000O0O0O ['id']=OO00OO0OO00OOO0O0 .id #line:160
        OO0OOOO00OO0OO000 .io_stats (O00O0OOOO000O0O0O ,OOO000O0000O0OO0O )#line:161
        OO0OOOO00OO0OO000 .net_stats (O00O0OOOO000O0O0O ,OOOOOOOOO0OO0O00O ,OOO000O0000O0OO0O )#line:162
        OO0OOOO00OO0OO000 .cpu_stats (O00O0OOOO000O0O0O ,OOO000O0000O0OO0O )#line:163
        OO0OOOO00OO0OO000 .mem_stats (O00O0OOOO000O0O0O ,OOO000O0000O0OO0O )#line:164
        public .cache_set ('stats',O00O0OOOO000O0O0O )#line:165
        OO0OOOO00OO0OO000 .__OOOO00OOO0O00O0O0 ['detail']=O00O0OOOO000O0O0O #line:166
        return public .returnMsg (True ,OO0OOOO00OO0OO000 .__OOOO00OOO0O00O0O0 )#line:167
    def write_cpu (O0OOO000OOOO00OO0 ,OO0O0O0OO0OOO0000 ):#line:169
        OOOO0OO0OOOO00O00 ={"time":time .time (),"cpu_usage":OO0O0O0OO0OOO0000 ['cpu_usage'],"online_cpus":OO0O0O0OO0OOO0000 ['online_cpus'],"container_id":OO0O0O0OO0OOO0000 ['container_id']}#line:175
        dp .sql ("cpu_stats").where ("time<?",(O0OOO000OOOO00OO0 .__OOOO00OOO0O00O0O0 ['expired'],)).delete ()#line:176
        dp .sql ("cpu_stats").insert (OOOO0OO0OOOO00O00 )#line:177
    def write_io (OOOO00O0O00OO0OO0 ,OOOOO000OOOOO00O0 ):#line:179
        O000OO0O000OOOOOO ={"time":time .time (),"write_total":OOOOO000OOOOO00O0 ['write_total'],"read_total":OOOOO000OOOOO00O0 ['read_total'],"container_id":OOOOO000OOOOO00O0 ['container_id']}#line:185
        dp .sql ("io_stats").where ("time<?",(OOOO00O0O00OO0OO0 .__OOOO00OOO0O00O0O0 ['expired'],)).delete ()#line:186
        dp .sql ("io_stats").insert (O000OO0O000OOOOOO )#line:187
    def write_net (O0000000OO0O00OO0 ,O0O0O00O0OO0OO0O0 ):#line:189
        O00O00OO0OO0OOOOO ={"time":time .time (),"tx_total":O0O0O00O0OO0OO0O0 ['tx_total'],"rx_total":O0O0O00O0OO0OO0O0 ['rx_total'],"tx":O0O0O00O0OO0OO0O0 ['tx'],"rx":O0O0O00O0OO0OO0O0 ['rx'],"container_id":O0O0O00O0OO0OO0O0 ['container_id']}#line:197
        dp .sql ("net_stats").where ("time<?",(O0000000OO0O00OO0 .__OOOO00OOO0O00O0O0 ['expired'],)).delete ()#line:198
        dp .sql ("net_stats").insert (O00O00OO0OO0OOOOO )#line:199
    def write_mem (OO0O00O0O000O00OO ,O0000OO0O0OOO00OO ):#line:201
        O00OOOOOOO000O00O ={"time":time .time (),"mem_limit":O0000OO0O0OOO00OO ['limit'],"cache":O0000OO0O0OOO00OO ['cache'],"usage":O0000OO0O0OOO00OO ['usage'],"usage_total":O0000OO0O0OOO00OO ['usage_total'],"container_id":O0000OO0O0OOO00OO ['container_id']}#line:209
        dp .sql ("mem_stats").where ("time<?",(OO0O00O0O000O00OO .__OOOO00OOO0O00O0O0 ['expired'],)).delete ()#line:210
        dp .sql ("mem_stats").insert (O00OOOOOOO000O00O )#line:211
    def get_container_count (O0OO00O0OOO0O0000 ,OO0OOOOOO0OO0O0OO ):#line:214
        O0O00OO0O0OOOO000 =OO0OOOOOO0OO0O0OO .url #line:215
        return len (O0OO00O0OOO0O0000 .docker_client (O0O00OO0O0OOOO000 ).containers .list ())#line:216

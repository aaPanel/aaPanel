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

import os
import json
import public
import projectModel.bt_docker.dk_public as dp

class main :#line:1
    def get_config (O0OO0OO0O0OOO0OOO ,O0OOOO000OOOO0000 ):#line:3
        import projectModel .bt_docker .dk_public as dp #line:4
        O00O0OOO0O0O0OO00 =O0OO0OO0O0OOO0OOO .get_registry_mirrors (O0OOOO000OOOO0000 )#line:6
        if not O00O0OOO0O0O0OO00 ["status"]:#line:7
            return O00O0OOO0O0O0OO00 #line:8
        else :#line:9
            O00O0OOO0O0O0OO00 =O00O0OOO0O0O0OO00 ['msg']#line:10
        OOO00O00O00000000 =O0OO0OO0O0OOO0OOO .get_service_status ()#line:11
        return public .returnMsg (True ,{"registry_mirrors":O00O0OOO0O0O0OO00 ,"service_status":OOO00O00O00000000 ,"installed":O0OO0OO0O0OOO0OOO .check_docker_program (),"monitor_status":O0OO0OO0O0OOO0OOO .get_monitor_status (),"monitor_save_date":dp .docker_conf ()['SAVE']})#line:18
    def set_monitor_save_date (O0OO0000000O0OO0O ,OO0OO0O0O00OO0OOO ):#line:20
        ""#line:25
        import re #line:26
        OOOO0O0OO00O00O00 ="{}/data/docker.conf".format (public .get_panel_path ())#line:27
        O00OO000O0OO0000O =public .readFile (OOOO0O0OO00O00O00 )#line:28
        try :#line:29
            OOO00O0000000OO0O =int (OO0OO0O0O00OO0OOO .save_date )#line:30
        except :#line:31
            return public .returnMsg (False ,"The monitoring save time needs to be a positive integer!")#line:32
        if OOO00O0000000OO0O >999 :#line:33
            return public .returnMsg (False ,"Monitoring data cannot be retained for more than 999 days!")#line:34
        if not O00OO000O0OO0000O :#line:35
            O00OO000O0OO0000O ="SAVE={}".format (OOO00O0000000OO0O )#line:36
            public .writeFile (OOOO0O0OO00O00O00 ,O00OO000O0OO0000O )#line:37
            return public .returnMsg (True ,"Set up successfully!")#line:38
        O00OO000O0OO0000O =re .sub (r"SAVE\s*=\s*\d+","SAVE={}".format (OOO00O0000000OO0O ),O00OO000O0OO0000O )#line:39
        public .writeFile (OOOO0O0OO00O00O00 ,O00OO000O0OO0000O )#line:40
        dp .write_log ("Set the monitoring time to [] days!".format (OOO00O0000000OO0O ))#line:41
        return public .returnMsg (True ,"Set up successfully!")#line:42
    def get_service_status (OO0O0OOOO00O0000O ):#line:44
        import projectModel .bt_docker .dk_public as dp #line:45
        OOOO0OO00O00O0O0O ='/var/run/docker.pid'#line:46
        if os .path .exists (OOOO0OO00O00O0O0O ):#line:47
            try :#line:48
                O0O0O0OOO0OO0OOOO =dp .docker_client ()#line:49
                if O0O0O0OOO0OO0OOOO :#line:50
                    return True #line:51
                else :#line:52
                    return False #line:53
            except :#line:54
                return False #line:55
        else :#line:56
            return False #line:57
    def docker_service (O00OOO000O0000O0O ,OOO00OO000000OOOO ):#line:60
        ""#line:65
        import public #line:66
        O000O0OOO0O0O000O ={'start':'start','stop':'stop','restart':'restart'}#line:67
        if OOO00OO000000OOOO .act not in O000O0OOO0O0O000O :#line:68
            return public .returnMsg (False ,'There is no way to do this!')#line:69
        O0000OO0O0OOOOOO0 ='systemctl {} docker'.format (OOO00OO000000OOOO .act )#line:70
        if OOO00OO000000OOOO .act =="stop":#line:71
            O0000OO0O0OOOOOO0 +="&& systemctl {} docker.socket".format (OOO00OO000000OOOO .act )#line:72
        public .ExecShell (O0000OO0O0OOOOOO0 )#line:73
        dp .write_log ("Set the Docker service status to [{}] successful".format (O000O0OOO0O0O000O [OOO00OO000000OOOO .act ]))#line:74
        return public .returnMsg (True ,"Set the status to [{}] successful".format (O000O0OOO0O0O000O [OOO00OO000000OOOO .act ]))#line:75
    def get_registry_mirrors (O000O0OO0O00O0000 ,OO00O0OOO000O00O0 ):#line:78
        try :#line:79
            if not os .path .exists ('/etc/docker/daemon.json'):#line:80
                return public .returnMsg (True ,[])#line:81
            O00000OOOOOOOO0O0 =json .loads (public .readFile ('/etc/docker/daemon.json'))#line:82
            if "registry-mirrors"not in O00000OOOOOOOO0O0 :#line:83
                return public .returnMsg (True ,[])#line:84
            return public .returnMsg (True ,O00000OOOOOOOO0O0 ['registry-mirrors'])#line:85
        except :#line:86
            return public .returnMsg (False ,'Get failed! Reason for failure: {}'.format (public .get_error_info ()))#line:87
    def set_registry_mirrors (OO0OO0000OO0OOOO0 ,OOOO000OO0O00O000 ):#line:90
        ""#line:95
        import re #line:96
        try :#line:97
            O0000O0O0O000O00O ={}#line:98
            if os .path .exists ('/etc/docker/daemon.json'):#line:99
                O0000O0O0O000O00O =json .loads (public .readFile ('/etc/docker/daemon.json'))#line:100
            if not OOOO000OO0O00O000 .registry_mirrors_address .strip ():#line:101
                if 'registry-mirrors'not in O0000O0O0O000O00O :#line:103
                    return public .returnMsg (True ,'Set successfully')#line:104
                del (O0000O0O0O000O00O ['registry-mirrors'])#line:105
            else :#line:106
                O0O0O0O00OOOO0O0O =OOOO000OO0O00O000 .registry_mirrors_address .strip ().split ('\n')#line:107
                for O0000OOO0OO0000O0 in O0O0O0O00OOOO0O0O :#line:108
                    if not re .search ('https?://',O0000OOO0OO0000O0 ):#line:109
                        return public .returnMsg (False ,'The acceleration address [{}] is malformed<br>Reference: https://mirror.ccs.tencentyun.com'.format (O0000OOO0OO0000O0 ))#line:110
                O0000O0O0O000O00O ['registry-mirrors']=O0O0O0O00OOOO0O0O #line:112
            public .writeFile ('/etc/docker/daemon.json',json .dumps (O0000O0O0O000O00O ,indent =2 ))#line:115
            dp .write_log ("Set up Docker acceleration successfully!")#line:116
            return public .returnMsg (True ,'Set successfully')#line:117
        except :#line:118
            return public .returnMsg (False ,'Setup failed! Reason for failure:{}'.format (public .get_error_info ()))#line:119
    def get_monitor_status (OO0O00O0OO0O0O000 ):#line:121
        ""#line:124
        O00O000O00OO00000 =public .process_exists ("python",cmdline ="/www/server/panel/class/projectModel/bt_docker/dk_monitor.py")#line:126
        if O00O000O00OO00000 :#line:127
            return O00O000O00OO00000 #line:128
        O00O000O00OO00000 =public .process_exists ("python3",cmdline ="/www/server/panel/class/projectModel/bt_docker/dk_monitor.py")#line:129
        if O00O000O00OO00000 :#line:130
            return O00O000O00OO00000 #line:131
        return O00O000O00OO00000 #line:132
    def set_docker_monitor (OO0OOOOOOO0O00OO0 ,O0O0O0000O0OOO000 ):#line:134
        ""#line:139
        import time #line:140
        import projectModel .bt_docker .dk_public as dp #line:141
        OOO000O0O0O0OOOO0 ="/www/server/panel/pyenv/bin/python"#line:142
        if not os .path .exists (OOO000O0O0O0OOOO0 ):#line:143
            OOO000O0O0O0OOOO0 ="/www/server/panel/pyenv/bin/python3"#line:144
        O0O000O0O00O0O000 ="/www/server/panel/class/projectModel/bt_docker/dk_monitor.py"#line:145
        if O0O0O0000O0OOO000 .act =="start":#line:146
            OOO0O00OO0OO0O00O ="nohup {} {} &".format (OOO000O0O0O0OOOO0 ,O0O000O0O00O0O000 )#line:147
            public .ExecShell (OOO0O00OO0OO0O00O )#line:148
            time .sleep (1 )#line:149
            if OO0OOOOOOO0O00OO0 .get_monitor_status ():#line:150
                dp .write_log ("Docker monitoring started successfully!")#line:151
                return public .returnMsg (True ,"Start monitoring successfully!")#line:152
            return public .returnMsg (False ,"Failed to start monitoring!")#line:153
        else :#line:154
            O0O0OOOOOOOO0O0OO =dp .get_process_id ("python","/www/server/panel/class/projectModel/bt_docker/dk_monitor.py")#line:155
            if not O0O0OOOOOOOO0O0OO :#line:156
                O0O0OOOOOOOO0O0OO =dp .get_process_id ("python3","/www/server/panel/class/projectModel/bt_docker/dk_monitor.py")#line:157
            public .ExecShell ("kill -9 {}".format (O0O0OOOOOOOO0O0OO ))#line:158
            dp .write_log ("Docker monitoring stopped successfully!")#line:159
            return public .returnMsg (True ,"Stop monitoring successfully!")#line:160
    def check_docker_program (O0O00O00OOOO0O000 ):#line:162
        ""#line:166
        O0O0O00O000OOO000 ="/usr/bin/docker"#line:167
        O00OO00OO0OOOOOO0 ="/usr/bin/docker-compose"#line:168
        if not os .path .exists (O0O0O00O000OOO000 )or not os .path .exists (O00OO00OO0OOOOOO0 ):#line:169
            return False #line:170
        return True #line:171
    def install_docker_program (OOO0000OOO0O0O0O0 ,O0O000O0OO000OO0O ):#line:173
        ""#line:178
        import time #line:179
        O000O000O0OO00O00 ="Install Docker service"#line:180
        O00O000OOOOOOO000 ="/bin/bash /www/server/panel/install/install_soft.sh 0 install docker_install_en"#line:183
        public .M ('tasks').add ('id,name,type,status,addtime,execstr',(None ,O000O000O0OO00O00 ,'execshell','0',time .strftime ('%Y-%m-%d %H:%M:%S'),O00O000OOOOOOO000 ))#line:184
        public .httpPost (public .GetConfigValue ('home')+'/api/panel/plugin_total',{"pid":"1111111",'p_name':"Docker商用模块"},3 )#line:185
        public.arequests('post', '{}/api/setupCount/setupPlugin'.format(public.OfficialApiBase()),
                         data={"pid": "1111111", 'p_name': "Dockerpaymodel"}, timeout=3)

        return public .returnMsg (True ,"Install task added to queue!")#line:186

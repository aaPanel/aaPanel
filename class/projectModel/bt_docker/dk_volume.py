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
import public
import projectModel.bt_docker.dk_public as dp
import docker.errors

class main :#line:1
    __O0O0O00O00OOO00O0 =None #line:3
    def docker_client (OO0000OOOO0O00000 ,O00000O0O00OO0O0O ):#line:5
        import projectModel .bt_docker .dk_public as dp #line:6
        return dp .docker_client (O00000O0O00OO0O0O )#line:7
    def get_volume_container_name (O0O000O0OOO00O0O0 ,O0O00OOOOO0O0O00O ):#line:10
        OO000OO00OOOOOOO0 =O0O000O0OOO00O0O0 .docker_client (O0O000O0OOO00O0O0 .__O0O0O00O00OOO00O0 ).containers #line:11
        O0O0OOOO00000OO0O =OO000OO00OOOOOOO0 .list (all =True )#line:12
        O0000O00OOOO00O00 =[O000OO00OOOO00O0O .attrs for O000OO00OOOO00O0O in O0O0OOOO00000OO0O ]#line:14
        for O00OOO00000OO0OOO in O0000O00OOOO00O00 :#line:15
            if not O00OOO00000OO0OOO ['Mounts']:#line:16
                continue #line:17
            for O0O00O0O0OOO000OO in O00OOO00000OO0OOO ['Mounts']:#line:18
                if "Name"not in O0O00O0O0OOO000OO :#line:19
                    continue #line:20
                if O0O00OOOOO0O0O00O ['Name']==O0O00O0O0OOO000OO ['Name']:#line:21
                    O0O00OOOOO0O0O00O ['container']=O00OOO00000OO0OOO ['Name'].replace ("/","")#line:22
        if 'container'not in O0O00OOOOO0O0O00O :#line:23
            O0O00OOOOO0O0O00O ['container']=''#line:24
        return O0O00OOOOO0O0O00O #line:25
    def get_volume_list (O0O0OOO0OO000000O ,OO0OO0O0OOOO0OO0O ):#line:27
        ""#line:31
        import projectModel .bt_docker .dk_setup as ds #line:32
        O0O0OOO0OO000000O .__O0O0O00O00OOO00O0 =OO0OO0O0OOOO0OO0O .url #line:33
        O0O0O0OOO0OOO0O00 =O0O0OOO0OO000000O .docker_client (OO0OO0O0OOOO0OO0O .url )#line:34
        O0O000O0OOOOOO00O =ds .main ()#line:35
        OO0OO00000OOOOOO0 =O0O000O0OOOOOO00O .check_docker_program ()#line:36
        OOOOO0OOOO000OOOO =O0O000O0OOOOOO00O .get_service_status ()#line:37
        if not O0O0O0OOO0OOO0O00 :#line:38
            O000O0000OOO000OO ={"volume":[],"installed":OO0OO00000OOOOOO0 ,"service_status":OOOOO0OOOO000OOOO }#line:43
            return public .returnMsg (True ,O000O0000OOO000OO )#line:44
        OO00O00OOO0O000O0 =O0O0O0OOO0OOO0O00 .volumes #line:45
        O000O0000OOO000OO ={"volume":O0O0OOO0OO000000O .get_volume_attr (OO00O00OOO0O000O0 ),"installed":OO0OO00000OOOOOO0 ,"service_status":OOOOO0OOOO000OOOO }#line:51
        return public .returnMsg (True ,O000O0000OOO000OO )#line:52
    def get_volume_attr (O00O000OO00000O00 ,O0O0OO0OO0OO0O0OO ):#line:54
        OOO00O0O0000O0O0O =O0O0OO0OO0OO0O0OO .list ()#line:55
        O00O00OOOOO00O000 =list ()#line:56
        for OO0OOOOOOOOO0OO00 in OOO00O0O0000O0O0O :#line:57
            OO0OOOOOOOOO0OO00 =O00O000OO00000O00 .get_volume_container_name (OO0OOOOOOOOO0OO00 .attrs )#line:58
            O00O00OOOOO00O000 .append (OO0OOOOOOOOO0OO00 )#line:59
        return O00O00OOOOO00O000 #line:60
    def add (O000O0OOOO0O0OOOO ,O0OO00O0O0OO0O0OO ):#line:62
        ""#line:70
        O000O0OOOO0O0OOOO .docker_client (O0OO00O0O0OO0O0OO .url ).volumes .create (name =O0OO00O0O0OO0O0OO .name ,driver =O0OO00O0O0OO0O0OO .driver ,driver_opts =O0OO00O0O0OO0O0OO .driver_opts if O0OO00O0O0OO0O0OO .driver_opts else None ,labels =dp .set_kv (O0OO00O0O0OO0O0OO .labels ))#line:76
        dp .write_log ("Adding storage volume [[]] succeeded!".format (O0OO00O0O0OO0O0OO .name ))#line:77
        return public .returnMsg (True ,"Added successfully!")#line:78
    def remove (O0OOO000000OO0OOO ,O0OO00OO0OOO00000 ):#line:80
        ""#line:86
        try :#line:87
            O0000O0OO000O0O0O =O0OOO000000OO0OOO .docker_client (O0OO00OO0OOO00000 .url ).volumes .get (O0OO00OO0OOO00000 .name )#line:88
            O0000O0OO000O0O0O .remove ()#line:89
            dp .write_log ("Delete storage volume [[]] successful!".format (O0OO00OO0OOO00000 .name ))#line:90
            return public .returnMsg (True ,"Successfully deleted")#line:91
        except docker .errors .APIError as OO00OO0O000O0O0O0 :#line:92
            if "volume is in use"in str (OO00OO0O000O0O0O0 ):#line:93
                return public .returnMsg (False ,"Storage volume is in use and cannot be deleted!")#line:94
            return public .returnMsg (False ,"Failed to delete! {}".format (OO00OO0O000O0O0O0 ))#line:95

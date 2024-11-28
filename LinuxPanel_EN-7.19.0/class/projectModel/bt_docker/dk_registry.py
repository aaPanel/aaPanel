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
import public #line:1
import os #line:2
import json #line:3
import projectModel .bt_docker .dk_public as dp #line:4
class main :#line:6
    def docker_client (O0OOOO000OOOO0OOO ,O0OO0000O00OO0OO0 ):#line:8
        return dp .docker_client (O0OO0000O00OO0OO0 )#line:9
    def add (O0OOO0OO00OO0O0O0 ,OOO0000O0O000O0OO ):#line:11
        ""#line:22
        if not OOO0000O0O000O0OO .registry :#line:24
            OOO0000O0O000O0OO .registry ="docker.io"#line:25
        O000O00O000O0O00O =O0OOO0OO00OO0O0O0 .login (OOO0000O0O000O0OO .url ,OOO0000O0O000O0OO .registry ,OOO0000O0O000O0OO .username ,OOO0000O0O000O0OO .password )#line:26
        if not O000O00O000O0O00O ['status']:#line:27
            return O000O00O000O0O00O #line:28
        O000OO0O00OO00OOO =O0OOO0OO00OO0O0O0 .registry_list ("get")['msg']['registry']#line:29
        for OOOOOOO0O000O0OOO in O000OO0O00OO00OOO :#line:30
            if OOOOOOO0O000O0OOO ['name']==OOO0000O0O000O0OO .name :#line:31
                return public .returnMsg (False ,"Name already exists! <br><br>Name: {}".format (OOO0000O0O000O0OO .name ))#line:32
            if OOOOOOO0O000O0OOO ['username']==OOO0000O0O000O0OO .username and OOO0000O0O000O0OO .registry ==OOOOOOO0O000O0OOO ['url']:#line:33
                return public .returnMsg (False ,"The repository information already exists!")#line:34
        O0OO0000OOO0OO00O ={"name":OOO0000O0O000O0OO .name ,"url":OOO0000O0O000O0OO .registry ,"namespace":OOO0000O0O000O0OO .namespace ,"username":OOO0000O0O000O0OO .username ,"password":OOO0000O0O000O0OO .password ,"remark":OOO0000O0O000O0OO .remark }#line:42
        dp .sql ("registry").insert (O0OO0000OOO0OO00O )#line:43
        dp .write_log ("Add repository [{}] [{}] successful!".format (OOO0000O0O000O0OO .name ,OOO0000O0O000O0OO .registry ))#line:44
        return public .returnMsg (True ,"Added successfully!")#line:45
    def edit (O0O0O0O000O00OOO0 ,O0O000OO000000OOO ):#line:47
        ""#line:58
        if str (O0O000OO000000OOO .id )=="1":#line:60
            return public .returnMsg (False ,"[Docker official repository] cannot be edited!")#line:61
        if not O0O000OO000000OOO .registry :#line:62
            O0O000OO000000OOO .registry ="docker.io"#line:63
        O00O00O0O0O0000OO =O0O0O0O000O00OOO0 .login (O0O000OO000000OOO .url ,O0O000OO000000OOO .registry ,O0O000OO000000OOO .username ,O0O000OO000000OOO .password )#line:64
        if not O00O00O0O0O0000OO ['status']:#line:65
            return O00O00O0O0O0000OO #line:66
        O00O00O0O0O0000OO =dp .sql ("registry").where ("id=?",(O0O000OO000000OOO .id ,)).find ()#line:67
        if not O00O00O0O0O0000OO :#line:68
            return public .returnMsg (False ,"This repository was not found")#line:69
        OO0OOOOO0O000OOOO ={"name":O0O000OO000000OOO .name ,"url":O0O000OO000000OOO .registry ,"username":O0O000OO000000OOO .username ,"password":O0O000OO000000OOO .password ,"namespace":O0O000OO000000OOO .namespace ,"remark":O0O000OO000000OOO .remark }#line:77
        dp .sql ("registry").where ("id=?",(O0O000OO000000OOO .id ,)).update (OO0OOOOO0O000OOOO )#line:78
        dp .write_log ("Editing repository [{}][{}] succeeded!".format (O0O000OO000000OOO .name ,O0O000OO000000OOO .registry ))#line:79
        return public .returnMsg (True ,"Edited successfully!")#line:80
    def remove (OO0OO00O00OO0O000 ,O0O00O0OO0000OO00 ):#line:82
        ""#line:88
        if str (O0O00O0OO0000OO00 .id )=="1":#line:89
            return public .returnMsg (False ,"[Docker official repository] cannot be deleted!")#line:90
        OO00O0OO00000000O =dp .sql ("registry").where ("id=?",(O0O00O0OO0000OO00 .id )).find ()#line:91
        dp .sql ("registry").where ("id=?",(O0O00O0OO0000OO00 .id ,)).delete ()#line:92
        dp .write_log ("Deleting repository [{}][{}] succeeded!".format (OO00O0OO00000000O ['name'],OO00O0OO00000000O ['url']))#line:93
        return public .returnMsg (True ,"Successfully deleted!")#line:94
    def registry_list (OO0OOOO0000O00OOO ,O000OO0O00OO0O0OO ):#line:96
        ""#line:100
        import projectModel .bt_docker .dk_setup as ds #line:101
        OO0OO0000OO0O0O00 =dp .sql ("registry").select ()#line:102
        if not isinstance (OO0OO0000OO0O0O00 ,list ):#line:103
            OO0OO0000OO0O0O00 =[]#line:104
        OOOO0OO000O000O00 =ds .main ()#line:105
        OO0O0O0OOO0O0000O ={"registry":OO0OO0000OO0O0O00 ,"installed":OOOO0OO000O000O00 .check_docker_program (),"service_status":OOOO0OO000O000O00 .get_service_status ()}#line:110
        return public .returnMsg (True ,OO0O0O0OOO0O0000O )#line:111
    def registry_info (OOO0OO0O0OOOO0O00 ,O0OOO00O0O00000OO ):#line:113
        return dp .sql ("registry").where ("name=?",(O0OOO00O0O00000OO ,)).find ()#line:114
    def login (O0O0OO0O000000O00 ,OO00O00O0O0OOOOO0 ,OO0O000O000O00000 ,O0OOO000000000O00 ,O00OO0O00O000OO0O ):#line:116
        ""#line:121
        import docker .errors #line:122
        try :#line:123
            O0OOO0OO00OOOOOO0 =O0O0OO0O000000O00 .docker_client (OO00O00O0O0OOOOO0 ).login (registry =OO0O000O000O00000 ,username =O0OOO000000000O00 ,password =O00OO0O00O000OO0O ,reauth =False )#line:129
            return public .returnMsg (True ,str (O0OOO0OO00OOOOOO0 ))#line:130
        except docker .errors .APIError as OOOO0OOO0O00O0000 :#line:131
            if "unauthorized: incorrect username or password"in str (OOOO0OOO0O00O0000 ):#line:132
                return public .returnMsg (False ,"Login test failed! <br><br>Reason: The account password is incorrect! {}".format (OOOO0OOO0O00O0000 ))#line:133
            return public .returnMsg (False ,"Login test failed! <br><br>Reason: {}".format (OOOO0OOO0O00O0000 ))
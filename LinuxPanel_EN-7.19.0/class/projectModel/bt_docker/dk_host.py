# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------
import public #line:1
import projectModel .bt_docker .dk_public as dp #line:2
class main :#line:4
    def get_list (O0000O0OOO0OO0O00 ,args =None ):#line:7
        OO000O0OOO00OO00O =dp .sql ("hosts").select ()#line:8
        for OO0000O00OOO0OOO0 in OO000O0OOO00OO00O :#line:9
            if dp .docker_client (OO0000O00OOO0OOO0 ['url']):#line:10
                OO0000O00OOO0OOO0 ['status']=True #line:11
            else :#line:12
                OO0000O00OOO0OOO0 ['status']=False #line:13
        return OO000O0OOO00OO00O #line:14
    def add (O0OO00O0O000O0000 ,O00O0000O00000O0O ):#line:17
        ""#line:22
        import time #line:23
        O00OO0OOO000OO0O0 =O0OO00O0O000O0000 .get_list ()#line:24
        for O0O0OO00O00OOOOOO in O00OO0OOO000OO0O0 :#line:25
            if O0O0OO00O00OOOOOO ['url']==O00O0000O00000O0O .url :#line:26
                return public .returnMsg (False ,"This host already exists!")#line:27
        if not dp .docker_client (O00O0000O00000O0O .url ):#line:29
            return public .returnMsg (False ,"Failed to connect to the server, please check if docker has been started!")#line:30
        O0O0OO0OOOOO0OOO0 ={"url":O00O0000O00000O0O .url ,"remark":O00O0000O00000O0O .remark ,"time":int (time .time ())}#line:35
        dp .write_log ("Add host [{}] successful!".format (O00O0000O00000O0O .url ))#line:36
        dp .sql ('hosts').insert (O0O0OO0OOOOO0OOO0 )#line:37
        return public .returnMsg (True ,"Add docker host successfully!")#line:38
    def delete (O0OOOO0000000O00O ,O0O0O0O000000OOOO ):#line:40
        ""#line:44
        OOO00OO0OO0OOO00O =dp .sql ('hosts').where ('id=?',O0O0O0O000000OOOO (O0O0O0O000000OOOO .id ,)).find ()#line:45
        dp .sql ('hosts').delete (id =O0O0O0O000000OOOO .id )#line:46
        dp .write_log ("Delete host [{}] succeeded!".format (OOO00OO0OO0OOO00O ['url']))#line:47
        return public .returnMsg (True ,"Delete host successfully!")
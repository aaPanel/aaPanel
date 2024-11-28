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
import projectModel .bt_docker .dk_public as dp #line:2
import docker .errors #line:3
class main :#line:5
    def docker_client (O00O0O000OO0000O0 ,OOO0OOOO0O0000OO0 ):#line:7
        import projectModel .bt_docker .dk_public as dp #line:8
        return dp .docker_client (OOO0OOOO0O0000OO0 )#line:9
    def get_host_network (OO0O00O000O000O0O ,O00OO00OO00OOOOOO ):#line:11
        ""#line:16
        import projectModel .bt_docker .dk_setup as ds #line:17
        O00OO00O00000000O =ds .main ()#line:18
        O000O0O0O00OO000O =O00OO00O00000000O .check_docker_program ()#line:19
        O0O00O000OOO0OO0O =O00OO00O00000000O .get_service_status ()#line:20
        OO0O0O00OO0OO0OO0 =OO0O00O000O000O0O .docker_client (O00OO00OO00OOOOOO .url )#line:21
        if not OO0O0O00OO0OO0OO0 :#line:22
            O0000O0000O0O0OO0 ={"images_list":[],"registry_list":[],"installed":O000O0O0O00OO000O ,"service_status":O0O00O000OOO0OO0O }#line:28
            return public .returnMsg (True ,O0000O0000O0O0OO0 )#line:29
        O000OO0OO00OOOO0O =OO0O0O00OO0OO0OO0 .networks #line:30
        O0OOO0O00O00OO000 =OO0O00O000O000O0O .get_network_attr (O000OO0OO00OOOO0O )#line:31
        O0000O0000O0O0OO0 =list ()#line:32
        for OOOO0O0OOOO0O00O0 in O0OOO0O00O00OO000 :#line:33
            OOOO00OOOO0O0000O =""#line:34
            O00O000OOOO000O0O =""#line:35
            if OOOO0O0OOOO0O00O0 ["IPAM"]["Config"]:#line:36
                if "Subnet"in OOOO0O0OOOO0O00O0 ["IPAM"]["Config"][0 ]:#line:37
                    OOOO00OOOO0O0000O =OOOO0O0OOOO0O00O0 ["IPAM"]["Config"][0 ]["Subnet"]#line:38
                if "Gateway"in OOOO0O0OOOO0O00O0 ["IPAM"]["Config"][0 ]:#line:39
                    O00O000OOOO000O0O =OOOO0O0OOOO0O00O0 ["IPAM"]["Config"][0 ]["Gateway"]#line:40
            OOOOO000000OO000O ={"id":OOOO0O0OOOO0O00O0 ["Id"],"name":OOOO0O0OOOO0O00O0 ["Name"],"time":OOOO0O0OOOO0O00O0 ["Created"],"driver":OOOO0O0OOOO0O00O0 ["IPAM"]["Driver"],"subnet":OOOO00OOOO0O0000O ,"gateway":O00O000OOOO000O0O ,"labels":OOOO0O0OOOO0O00O0 ["Labels"]}#line:49
            O0000O0000O0O0OO0 .append (OOOOO000000OO000O )#line:50
        OOOOOOO000O0O0O0O ={"network":O0000O0000O0O0OO0 ,"installed":O000O0O0O00OO000O ,"service_status":O0O00O000OOO0OO0O }#line:56
        return public .returnMsg (True ,OOOOOOO000O0O0O0O )#line:57
    def get_network_attr (OO0O00O00O000OO00 ,O0OO0000O0OOO0O0O ):#line:59
        O000OOOO0OOO00O00 =O0OO0000O0OOO0O0O .list ()#line:60
        return [O00O0000O0OO00O00 .attrs for O00O0000O0OO00O00 in O000OOOO0OOO00O00 ]#line:61
    def add (O0OOO0O0O0000OO0O ,O0OOO0O000000000O ):#line:63
        ""#line:75
        import docker #line:76
        O0O0000OO00OO00OO =docker .types .IPAMPool (subnet =O0OOO0O000000000O .subnet ,gateway =O0OOO0O000000000O .gateway ,iprange =O0OOO0O000000000O .iprange )#line:81
        OOOO00000O000OO0O =docker .types .IPAMConfig (pool_configs =[O0O0000OO00OO00OO ])#line:84
        O0OOO0O0O0000OO0O .docker_client (O0OOO0O000000000O .url ).networks .create (name =O0OOO0O000000000O .name ,options =O0OOO0O000000000O .options if O0OOO0O000000000O .options else None ,driver ="bridge",ipam =OOOO00000O000OO0O ,labels =dp .set_kv (O0OOO0O000000000O .labels ))#line:91
        dp .write_log ("Add network [{}] [{}] successful!".format (O0OOO0O000000000O .name ,O0OOO0O000000000O .iprange ))#line:92
        return public .returnMsg (True ,"Added successfully!")#line:93
    def del_network (OOOOO0OO0O00O000O ,OOO0OOOO0O0O0O0O0 ):#line:95
        ""#line:100
        try :#line:101
            O000O0OO00O0OO000 =OOOOO0OO0O00O000O .docker_client (OOO0OOOO0O0O0O0O0 .url ).networks .get (OOO0OOOO0O0O0O0O0 .id )#line:103
            O0OOOOOO0OO0O0OOO =O000O0OO00O0OO000 .attrs #line:104
            if O0OOOOOO0OO0O0OOO ['Name']in ["bridge","none"]:#line:105
                return public .returnMsg (False ,"The system default network cannot be deleted!")#line:106
            O000O0OO00O0OO000 .remove ()#line:107
            dp .write_log ("Delete network [{}] successful!".format (O0OOOOOO0OO0O0OOO ['Name']))#line:108
            return public .returnMsg (True ,"Successfully deleted!")#line:109
        except docker .errors .APIError as OOOOOO0O00O0O0OO0 :#line:110
            if " has active endpoints"in str (OOOOOO0O00O0O0OO0 ):#line:111
                return public .returnMsg (False ,"The network is in use and cannot be deleted!")#line:112
            return public .returnMsg (False ,"Failed to delete! {}".format (str (OOOOOO0O00O0O0OO0 )))
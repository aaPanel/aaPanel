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

import db #line:1
import public #line:2
import json #line:3
def sql (O000O0O0O00000OO0 ):#line:5
    with db .Sql ()as O000000OOO00O0000 :#line:6
        O000000OOO00O0000 .dbfile ("docker")#line:7
        return O000000OOO00O0000 .table (O000O0O0O00000OO0 )#line:8
def docker_client (url ="unix:///var/run/docker.sock"):#line:11
    import docker #line:12
    """
    目前仅支持本地服务器
    :param url: unix:///var/run/docker.sock
    :return:
    """#line:17
    try :#line:18
        O00O00O00000OO0OO =docker .DockerClient (base_url =url )#line:19
        O00O00O00000OO0OO .networks .list ()#line:20
        return O00O00O00000OO0OO #line:21
    except :#line:22
        return False #line:23
def docker_client_low (url ="unix:///var/run/docker.sock"):#line:25
    ""#line:30
    import docker #line:31
    try :#line:32
        O0OO0000000O0OOOO =docker .APIClient (base_url =url )#line:33
        return O0OO0000000O0OOOO #line:34
    except docker .errors .DockerException :#line:35
        return False #line:36
def get_cpu_count ():#line:39
    import re #line:40
    OOO00O00O0000O00O =open ('/proc/cpuinfo','r').read ()#line:41
    OO00O0000OO000OOO =r"processor\s*:"#line:42
    OO0OOO0O00O0O0OOO =re .findall (OO00O0000OO000OOO ,OOO00O00O0000O00O )#line:43
    if not OO0OOO0O00O0O0OOO :#line:44
        return 0 #line:45
    return len (OO0OOO0O00O0O0OOO )#line:46
def set_kv (OO0OO0OOO0O00O0OO ):#line:48
    ""#line:53
    if not OO0OO0OOO0O00O0OO :#line:54
        return None #line:55
    O00OOOOO0O0OOOO00 =OO0OO0OOO0O00O0OO .split ('\n')#line:56
    O000OOO0OO00O00OO =dict ()#line:57
    for OOOOO0OO00OO0O0OO in O00OOOOO0O0OOOO00 :#line:58
        OOOOO0OO00OO0O0OO =OOOOO0OO00OO0O0OO .strip ()#line:59
        if not OOOOO0OO00OO0O0OO :#line:60
            continue #line:61
        OOO00OO000O000000 ,OO00O0O00000OOO00 =OOOOO0OO00OO0O0OO .split ('=')#line:62
        O000OOO0OO00O00OO [OOO00OO000O000000 ]=OO00O0O00000OOO00 #line:63
    return O000OOO0OO00O00OO #line:64
def get_mem_info ():#line:66
    import psutil #line:68
    O0O0OOO000OO0OOO0 =psutil .virtual_memory ()#line:69
    O00OOO0O0O00O0O0O =int (O0O0OOO000OO0OOO0 .total )#line:70
    return O00OOO0O0O00O0O0O #line:71
def byte_conversion (OO000000O00OOO0O0 ):#line:73
    if "b"in OO000000O00OOO0O0 :#line:74
        return int (OO000000O00OOO0O0 .replace ('b',''))#line:75
    elif "KB"in OO000000O00OOO0O0 :#line:76
        return int (OO000000O00OOO0O0 .replace ('KB',''))*1024 #line:77
    elif "MB"in OO000000O00OOO0O0 :#line:78
        return int (OO000000O00OOO0O0 .replace ('MB',''))*1024 *1024 #line:79
    elif "GB"in OO000000O00OOO0O0 :#line:80
        return int (OO000000O00OOO0O0 .replace ('GB',''))*1024 *1024 *1024 #line:81
    else :#line:82
        return False #line:83
def log_docker (OO000O00O0OOO0000 ,O0OO0O0O0O0OOO0O0 ):#line:85
    __OO0000000OO0OO0O0 ='/tmp/dockertmp.log'#line:86
    while True :#line:87
        try :#line:88
            O000O0OOOOO0OOOO0 =OO000O00O0OOO0000 .__next__ ()#line:89
            try :#line:90
                O000O0OOOOO0OOOO0 =json .loads (O000O0OOOOO0OOOO0 )#line:91
                if 'status'in O000O0OOOOO0OOOO0 :#line:92
                    O0OOO00OO0O0OO00O ="{}\n".format (O000O0OOOOO0OOOO0 ['status'])#line:93
                    public .writeFile (__OO0000000OO0OO0O0 ,O0OOO00OO0O0OO00O ,'a+')#line:94
            except :#line:95
                public .writeFile (__OO0000000OO0OO0O0 ,public .get_error_info (),'a+')#line:96
            if 'stream'in O000O0OOOOO0OOOO0 :#line:97
                O0OOO00OO0O0OO00O =O000O0OOOOO0OOOO0 ['stream']#line:98
                public .writeFile (__OO0000000OO0OO0O0 ,O0OOO00OO0O0OO00O ,'a+')#line:99
        except StopIteration :#line:100
            public .writeFile (__OO0000000OO0OO0O0 ,f'{O0OO0O0O0O0OOO0O0} complete.','a+')#line:101
            break #line:102
        except ValueError :#line:103
            public .writeFile (log_path ,f'Error parsing output from {O0OO0O0O0O0OOO0O0}: {O000O0OOOOO0OOOO0}','a+')#line:104
def docker_conf ():#line:106
    ""#line:112
    OO0OOO0000OO0000O =public .readFile ("{}/data/docker.conf".format (public .get_panel_path ()))#line:113
    if not OO0OOO0000OO0000O :#line:114
        return {"SAVE":30 }#line:115
    O0O0OOOO0000OO0OO =dict ()#line:116
    for OO0OOO0O0OOO000O0 in OO0OOO0000OO0000O .split ("\n"):#line:117
        if not OO0OOO0O0OOO000O0 :#line:118
            continue #line:119
        O0OOO00O0O0OOOO00 ,OOOO00O0OOO00O00O =OO0OOO0O0OOO000O0 .split ("=")#line:120
        if O0OOO00O0O0OOOO00 =="SAVE":#line:121
            OOOO00O0OOO00O00O =int (OOOO00O0OOO00O00O )#line:122
        O0O0OOOO0000OO0OO [O0OOO00O0O0OOOO00 ]=OOOO00O0OOO00O00O #line:123
    return O0O0OOOO0000OO0OO #line:124
def get_process_id (OOOO0000O00OO00OO ,O0OO0OO0OOO0OOOOO ):#line:126
    import psutil #line:127
    OOOO000O0000OO0OO =psutil .pids ()#line:128
    for OO000O0000OOOO0O0 in OOOO000O0000OO0OO :#line:129
        try :#line:130
            O0OOO0000OOOO00O0 =psutil .Process (OO000O0000OOOO0O0 )#line:131
            if O0OOO0000OOOO00O0 .name ()==OOOO0000O00OO00OO and O0OO0OO0OOO0OOOOO in O0OOO0000OOOO00O0 .cmdline ():#line:132
                return OO000O0000OOOO0O0 #line:133
        except :#line:134
            pass #line:135
    return False #line:136
def write_log (OOO0OO0O0O00OO0O0 ):#line:138
    public .WriteLog ("Docker module",OOO0OO0O0O00OO0O0 )#line:139
def check_socket (O0000O0O000O0O000 ):#line:141
    import socket #line:142
    OO0O0O0OO0OO0000O =socket .socket (socket .AF_INET ,socket .SOCK_STREAM )#line:143
    O0O0OO00OOOO000O0 =("127.0.0.1",int (O0000O0O000O0O000 ))#line:144
    O000O00OO00O0000O =OO0O0O0OO0OO0000O .connect_ex (O0O0OO00OOOO000O0 )#line:145
    OO0O0O0OO0OO0000O .close ()#line:146
    if O000O00OO00O0000O ==0 :#line:147
        return True #line:148
    else :#line:149
        return False
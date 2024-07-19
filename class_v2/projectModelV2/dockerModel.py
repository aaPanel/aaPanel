# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 项目管理控制器
# ------------------------------
import os ,public ,json ,re ,time #line:13
class main :#line:15
    def __init__ (O00000000O0OO000O ):#line:17
        pass #line:18
    def model (O0O0OOO0OO0OO00OO ,OO0O0O000O00O00O0 ):#line:20
        ""#line:29
        import panelPlugin #line:30
        OO00OO0OOOO0OO0O0 =public .to_dict_obj ({})#line:31
        OO00OO0OOOO0OO0O0 .focre =1 #line:32
        O0OO000000O0000O0 =panelPlugin .panelPlugin ().get_soft_list (OO00OO0OOOO0OO0O0 )#line:33
        __OO000O0000OO000OO =int (O0OO000000O0000O0 ['ltd'])>1 #line:34
        try :#line:40
            OO0O0O000O00O00O0 .def_name =OO0O0O000O00O00O0 .dk_def_name #line:41
            OO0O0O000O00O00O0 .mod_name =OO0O0O000O00O00O0 .dk_model_name #line:42
            if OO0O0O000O00O00O0 ['mod_name']in ['base']:return public .return_status_code (1000 ,'Wrong call!')#line:43
            public .exists_args ('def_name,mod_name',OO0O0O000O00O00O0 )#line:44
            if OO0O0O000O00O00O0 ['def_name'].find ('__')!=-1 :return public .return_status_code (1000 ,'The called method name cannot contain the "__" characterrong call!')#line:45
            if not re .match (r"^\w+$",OO0O0O000O00O00O0 ['mod_name']):return public .return_status_code (1000 ,r'The called module name cannot contain characters other than \w')#line:46
            if not re .match (r"^\w+$",OO0O0O000O00O00O0 ['def_name']):return public .return_status_code (1000 ,r'The called module name cannot contain characters other than \w')#line:47
        except :#line:48
            return public .get_error_object ()#line:49
        O0OOO0O0O00O00O0O ="dk_{}".format (OO0O0O000O00O00O0 ['mod_name'].strip ())#line:51
        OO00OO0OOOO0OOOOO =OO0O0O000O00O00O0 ['def_name'].strip ()#line:52
        OO00OO0O0OOOOO000 ="{}/projectModel/bt_docker/{}.py".format (public .get_class_path (),O0OOO0O0O00O00O0O )#line:55
        if not os .path .exists (OO00OO0O0OOOOO000 ):#line:56
            return public .return_status_code (1003 ,O0OOO0O0O00O00O0O )#line:57
        OO00O00OOOOOO0000 =public .get_script_object (OO00OO0O0OOOOO000 )#line:59
        if not OO00O00OOOOOO0000 :return public .return_status_code (1000 ,'{} model not found'.format (O0OOO0O0O00O00O0O ))#line:60
        OOO0O000O0OOOOO0O =getattr (OO00O00OOOOOO0000 .main (),OO00OO0OOOO0OOOOO ,None )#line:61
        if not OOO0O000O0OOOOO0O :return public .return_status_code (1000 ,'{} method not found in {} model'.format (O0OOO0O0O00O00O0O ,OO00OO0OOOO0OOOOO ))#line:62
        O00O0O00O000O0000 ='{}_{}_LAST'.format (O0OOO0O0O00O00O0O .upper (),OO00OO0OOOO0OOOOO .upper ())#line:76
        O0OO0OOOOO00OOOO0 =public .exec_hook (O00O0O00O000O0000 ,OO0O0O000O00O00O0 )#line:77
        if isinstance (O0OO0OOOOO00OOOO0 ,public .dict_obj ):#line:78
            OOO0OOOOOOO000O0O =O0OO0OOOOO00OOOO0 #line:79
        elif isinstance (O0OO0OOOOO00OOOO0 ,dict ):#line:80
            return O0OO0OOOOO00OOOO0 #line:81
        elif isinstance (O0OO0OOOOO00OOOO0 ,bool ):#line:82
            if not O0OO0OOOOO00OOOO0 :#line:83
                return public .return_data (False ,{},error_msg ='Pre-HOOK interrupt operation')#line:84
        OO000OOOO000OOO0O =OOO0O000O0OOOOO0O (OO0O0O000O00O00O0 )#line:87
        O00O0O00O000O0000 ='{}_{}_END'.format (O0OOO0O0O00O00O0O .upper (),OO00OO0OOOO0OOOOO .upper ())#line:90
        O0O000OO0O00O0OOO =public .to_dict_obj ({'args':OO0O0O000O00O00O0 ,'result':OO000OOOO000OOO0O })#line:94
        O0OO0OOOOO00OOOO0 =public .exec_hook (O00O0O00O000O0000 ,O0O000OO0O00O0OOO )#line:95
        if isinstance (O0OO0OOOOO00OOOO0 ,dict ):#line:96
            OO000OOOO000OOO0O =O0OO0OOOOO00OOOO0 ['result']#line:97
        return OO000OOOO000OOO0O #line:98

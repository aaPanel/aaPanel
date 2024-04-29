#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 磁盘配额管理
#------------------------------
import os ,public ,psutil ,json ,time ,re
from projectModel .base import projectBase 
class main (projectBase ):
    xfs_quota ="xfs_quota"
    __O0O000000OO000000 ='{}/config/quota.json'.format (public .get_panel_path ())
    __O00OOOO00OO0OO0OO ='{}/config/mysql_quota.json'.format (public .get_panel_path ())
    __O0O00000000OOO0O0 =public .to_string ([84 ,104 ,105 ,115 ,32 ,102 ,101 ,97 ,116 ,117 ,114 ,101 ,32 ,105 ,115 ,32 ,101 ,120 ,99 ,108 ,117 ,115 ,105 ,118 ,101 ,32 ,116 ,111 ,32 ,116 ,104 ,101 ,32 ,112 ,114 ,111 ,32 ,101 ,100 ,105 ,116 ,105 ,111 ,110 ,44 ,32 ,112 ,108 ,101 ,97 ,115 ,101 ,32 ,97 ,99 ,116 ,105 ,118 ,97 ,116 ,101 ,32 ,105 ,116 ,32 ,102 ,105 ,114 ,115 ,116 ])
    def __init__ (OOO0000OO0OO0O00O ):
        _O0OOO0O00O0O0O000 ='{}/data/quota_install.pl'.format (public .get_panel_path ())
        if not os .path .exists (_O0OOO0O00O0O0O000 ):
            O0OO0OOO0OO0O0O00 ='/usr/sbin/xfs_quota'
            if not os .path .exists (O0OO0OOO0OO0O0O00 ):
                if os .path .exists ('/usr/bin/apt-get'):
                    public .ExecShell ('nohup apt-get install xfsprogs -y > /dev/null &')
                else :
                    public .ExecShell ('nohup yum install xfsprogs -y > /dev/null &')
            public .writeFile (_O0OOO0O00O0O0O000 ,'True')
        if os .path .exists ("/sbin/xfs_quota"):
            OOO0000OO0OO0O00O .xfs_quota ="/sbin/xfs_quota"
    def __OO00OO00O0000O0OO (O00OOO0000000000O ,args =None ):
        ""
        OO00000OO0O00O0O0 =[]
        for OO00O0OO0O0000OOO in psutil .disk_partitions ():
            if OO00O0OO0O0000OOO .fstype =='xfs':
                OO00000OO0O00O0O0 .append ((OO00O0OO0O0000OOO .mountpoint ,OO00O0OO0O0000OOO .device ,psutil .disk_usage (OO00O0OO0O0000OOO .mountpoint ).free ,OO00O0OO0O0000OOO .opts .split (',')))
        return OO00000OO0O00O0O0 
    def __O00OOOO0OO00O0OO0 (O000O00O0O0000O00 ,args =None ):
        ""
        return O000O00O0O0000O00 .__O000O0O0000OOOOOO (args .path )
    def __O000000O0O0000OOO (O00OOO00000OOOO00 ,O000O00O00O00OOOO ):
        ""
        O0OOO000OO000OOO0 =O00OOO00000OOOO00 .__OO00OO00O0000O0OO ()
        OO0OO000OO00O0OO0 =None 
        for O0O0OOOO00O00OOO0 in O0OOO000OO000OOO0 :
            if O0O0OOOO00O00OOO0 [0 ]=="/":
                OO0OO000OO00O0OO0 =O0O0OOOO00O00OOO0 
            if O000O00O00O00OOOO .find (O0O0OOOO00O00OOO0 [0 ]+'/')==0 :
                if not 'prjquota'in O0O0OOOO00O00OOO0 [3 ]:
                    return O0O0OOOO00O00OOO0 
                return O0O0OOOO00O00OOO0 [1 ]
        if OO0OO000OO00O0OO0 and O000O00O00O00OOOO .find (OO0OO000OO00O0OO0 [0 ])==0 :
            if not 'prjquota'in OO0OO000OO00O0OO0 [3 ]:
                return OO0OO000OO00O0OO0 
            return OO0OO000OO00O0OO0 [1 ]
        return ''
    def __O000O0O0000OOOOOO (OO0OOO00OO000000O ,O0O0O0OOOOO0OOO0O ):
        ""
        if not os .path .exists (O0O0O0OOOOO0OOO0O ):return -1 
        if not os .path .isdir (O0O0O0OOOOO0OOO0O ):return -2 
        OO0O0OO0O0000000O =OO0OOO00OO000000O .__OO00OO00O0000O0OO ()
        O0O00OO00O0O0O00O =None 
        for O0OO0O0O00O00OO00 in OO0O0OO0O0000000O :
            if O0OO0O0O00O00OO00 [0 ]=="/":
                O0O00OO00O0O0O00O =O0OO0O0O00O00OO00 
            if O0O0O0OOOOO0OOO0O .find (O0OO0O0O00O00OO00 [0 ]+'/')==0 :
                return O0OO0O0O00O00OO00 [2 ]/1024 /1024 
        if O0O00OO00O0O0O00O and O0O0O0OOOOO0OOO0O .find (O0O00OO00O0O0O00O [0 ])==0 :
            return O0O00OO00O0O0O00O [2 ]/1024 /1024 
        return -3 
    def get_quota_path_list (OOOO000OO000O000O ,args =None ,get_path =None ):
        ""
        if not os .path .exists (OOOO000OO000O000O .__O0O000000OO000000 ):
            public .writeFile (OOOO000OO000O000O .__O0O000000OO000000 ,'[]')
        O00OO00OO000O0OO0 =json .loads (public .readFile (OOOO000OO000O000O .__O0O000000OO000000 ))
        OO00OOO0O00OOOO00 =[]
        for O0OOOO0O0O000O0O0 in O00OO00OO000O0OO0 :
            if not os .path .exists (O0OOOO0O0O000O0O0 ['path'])or not os .path .isdir (O0OOOO0O0O000O0O0 ['path'])or os .path .islink (O0OOOO0O0O000O0O0 ['path']):continue 
            if get_path :
                if O0OOOO0O0O000O0O0 ['path']==get_path :
                    OOO00OO0OOO0O0OO0 =psutil .disk_usage (O0OOOO0O0O000O0O0 ['path'])
                    O0OOOO0O0O000O0O0 ['used']=OOO00OO0OOO0O0OO0 .used 
                    O0OOOO0O0O000O0O0 ['free']=OOO00OO0OOO0O0OO0 .free 
                    return O0OOOO0O0O000O0O0 
                else :
                    continue 
            OOO00OO0OOO0O0OO0 =psutil .disk_usage (O0OOOO0O0O000O0O0 ['path'])
            O0OOOO0O0O000O0O0 ['used']=OOO00OO0OOO0O0OO0 .used 
            O0OOOO0O0O000O0O0 ['free']=OOO00OO0OOO0O0OO0 .free 
            OO00OOO0O00OOOO00 .append (O0OOOO0O0O000O0O0 )
        if get_path :
            return {'size':0 ,'used':0 ,'free':0 }
        if len (OO00OOO0O00OOOO00 )!=len (O00OO00OO000O0OO0 ):
            public .writeFile (OOOO000OO000O000O .__O0O000000OO000000 ,json .dumps (OO00OOO0O00OOOO00 ))
        return O00OO00OO000O0OO0 
    def get_quota_mysql_list (OO000O0O00OOOOO0O ,args =None ,get_name =None ):
        ""
        if not os .path .exists (OO000O0O00OOOOO0O .__O00OOOO00OO0OO0OO ):
            public .writeFile (OO000O0O00OOOOO0O .__O00OOOO00OO0OO0OO ,'[]')
        OO00OO0000O0O0OOO =json .loads (public .readFile (OO000O0O00OOOOO0O .__O00OOOO00OO0OO0OO ))
        O00O00OOO0OOO00OO =[]
        OOOO000000OO0O0O0 =public .M ('databases')
        for OOO0OO0O000O0O00O in OO00OO0000O0O0OOO :
            if get_name :
                if OOO0OO0O000O0O00O ['db_name']==get_name :
                    OOO0OO0O000O0O00O ['used']=OOO0OO0O000O0O00O ['used']=int (public .get_database_size_by_name (OOO0OO0O000O0O00O ['db_name']))
                    _O0OO00O000O0OOO00 =OOO0OO0O000O0O00O ['size']*1024 *1024 
                    if (OOO0OO0O000O0O00O ['used']>_O0OO00O000O0OOO00 and OOO0OO0O000O0O00O ['insert_accept'])or (OOO0OO0O000O0O00O ['used']<_O0OO00O000O0OOO00 and not OOO0OO0O000O0O00O ['insert_accept']):
                        OO000O0O00OOOOO0O .mysql_quota_check ()
                    return OOO0OO0O000O0O00O 
            else :
                if OOOO000000OO0O0O0 .where ('name=?',OOO0OO0O000O0O00O ['db_name']).count ():
                    if args :OOO0OO0O000O0O00O ['used']=int (public .get_database_size_by_name (OOO0OO0O000O0O00O ['db_name']))
                    O00O00OOO0OOO00OO .append (OOO0OO0O000O0O00O )
        OOOO000000OO0O0O0 .close ()
        if get_name :
            return {'size':0 ,'used':0 }
        if len (O00O00OOO0OOO00OO )!=len (OO00OO0000O0O0OOO ):
            public .writeFile (OO000O0O00OOOOO0O .__O00OOOO00OO0OO0OO ,json .dumps (O00O00OOO0OOO00OO ))
        return O00O00OOO0OOO00OO 
    def __OOO000O00000O0OO0 (OOOOOOOO0OOO000OO ,OOO0000OOO00O000O ,OO0OOO0000000OOO0 ,O0OOO0OO00O00O0OO ,OOOO00000OOOO0OO0 ):
        ""
        O0OO0O00O000O00O0 =OOO0000OOO00O000O .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O0OOO0OO00O00O0OO ,OO0OOO0000000OOO0 ,OOOO00000OOOO0OO0 ))
        if O0OO0O00O000O00O0 :raise public .PanelError ('Failed to remove insert permission for database user:{}'.format (O0OO0O00O000O00O0 ))
        O0OO0O00O000O00O0 =OOO0000OOO00O000O .execute ("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format (O0OOO0OO00O00O0OO ,OO0OOO0000000OOO0 ,OOOO00000OOOO0OO0 ))
        if O0OO0O00O000O00O0 :raise public .PanelError ('Failed to remove insert permission for database user:{}'.format (O0OO0O00O000O00O0 ))
        OOO0000OOO00O000O .execute ("FLUSH PRIVILEGES;")
        return True 
    def __O000O000O0OOOOOOO (OO00OOO00OO0OOO00 ,O000OOOO0OO0O00OO ,O0OOO0OOO0OO00O00 ,O00OOO0OO0OO0OOOO ,OOOOOOOO0OO00O000 ):
        ""
        OOO0O000OOOOO0O00 =O000OOOO0OO0O00OO .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O00OOO0OO0OO0OOOO ,O0OOO0OOO0OO00O00 ,OOOOOOOO0OO00O000 ))
        if OOO0O000OOOOO0O00 :raise public .PanelError ('Failed to restore insert privileges for database user:{}'.format (OOO0O000OOOOO0O00 ))
        OOO0O000OOOOO0O00 =O000OOOO0OO0O00OO .execute ("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format (O00OOO0OO0OO0OOOO ,O0OOO0OOO0OO00O00 ,OOOOOOOO0OO00O000 ))
        if OOO0O000OOOOO0O00 :raise public .PanelError ('Failed to restore insert privileges for database user:{}'.format (OOO0O000OOOOO0O00 ))
        O000OOOO0OO0O00OO .execute ("FLUSH PRIVILEGES;")
        return True 
    def mysql_quota_service (O00000OO00O0O0000 ):
        ""
        while 1 :
            time .sleep (600 )
            O00000OO00O0O0000 .mysql_quota_check ()
    def __O0OO00O00O0OOO0OO (O0OO0O0000OOO0O0O ,OO0O0OOOOO0O00O0O ):
        try :
            if type (OO0O0OOOOO0O00O0O )!=list and type (OO0O0OOOOO0O00O0O )!=str :OO0O0OOOOO0O00O0O =list (OO0O0OOOOO0O00O0O )
            return OO0O0OOOOO0O00O0O 
        except :return []
    def mysql_quota_check (OO0O0OOO00O0OO00O ):
        ""
        if not OO0O0OOO00O0OO00O .__OO000OOO0OO0O00OO ():return public .returnMsg (False ,OO0O0OOO00O0OO00O .__O0O00000000OOO0O0 )
        O00000OOO00OO000O =OO0O0OOO00O0OO00O .get_quota_mysql_list ()
        for OO0O0O0O0OO00OOO0 in O00000OOO00OO000O :
            try :
                if OO0O0O0O0OO00OOO0 ['size']<1 :
                    if not OO0O0O0O0OO00OOO0 ['insert_accept']:
                        OO0O0OOO00O0OO00O .__O000O000O0OOOOOOO (O0OOOO000OOO0O0OO ,O0000O00OO0O00O0O ,OO0O0O0O0OO00OOO0 ['db_name'],O000O00O0000OOO0O [0 ])
                        OO0O0O0O0OO00OOO0 ['insert_accept']=True 
                        public .WriteLog ('Quota','Database [{}] quota has been closed, restore insert privileges'.format (OO0O0O0O0OO00OOO0 ['db_name']))
                        continue 
                O000O000O00000O0O =public .get_database_size_by_name (OO0O0O0O0OO00OOO0 ['db_name'])/1024 /1024 
                O0000O00OO0O00O0O =public .M ('databases').where ('name=?',(OO0O0O0O0OO00OOO0 ['db_name'],)).getField ('username')
                O0OOOO000OOO0O0OO =public .get_mysql_obj (OO0O0O0O0OO00OOO0 ['db_name'])
                O0O0OOO0O0O00OOOO =OO0O0OOO00O0OO00O .__O0OO00O00O0OOO0OO (O0OOOO000OOO0O0OO .query ("select Host from mysql.user where User='"+O0000O00OO0O00O0O +"'"))
                if O000O000O00000O0O <OO0O0O0O0OO00OOO0 ['size']:
                    if not OO0O0O0O0OO00OOO0 ['insert_accept']:
                        for O000O00O0000OOO0O in O0O0OOO0O0O00OOOO :
                            OO0O0OOO00O0OO00O .__O000O000O0OOOOOOO (O0OOOO000OOO0O0OO ,O0000O00OO0O00O0O ,OO0O0O0O0OO00OOO0 ['db_name'],O000O00O0000OOO0O [0 ])
                        OO0O0O0O0OO00OOO0 ['insert_accept']=True 
                        public .WriteLog ('Quota','The database [{}] is below the quota [{}MB], restore the insert permission'.format (OO0O0O0O0OO00OOO0 ['db_name'],OO0O0O0O0OO00OOO0 ['size']))
                    if hasattr (O0OOOO000OOO0O0OO ,'close'):O0OOOO000OOO0O0OO .close ()
                    continue 
                if OO0O0O0O0OO00OOO0 ['insert_accept']:
                    for O000O00O0000OOO0O in O0O0OOO0O0O00OOOO :
                        OO0O0OOO00O0OO00O .__OOO000O00000O0OO0 (O0OOOO000OOO0O0OO ,O0000O00OO0O00O0O ,OO0O0O0O0OO00OOO0 ['db_name'],O000O00O0000OOO0O [0 ])
                    OO0O0O0O0OO00OOO0 ['insert_accept']=False 
                    public .WriteLog ('Quota','Database [{}] removed insert permission due to exceeding quota [{}MB]'.format (OO0O0O0O0OO00OOO0 ['db_name'],OO0O0O0O0OO00OOO0 ['size']))
                if hasattr (O0OOOO000OOO0O0OO ,'close'):O0OOOO000OOO0O0OO .close ()
            except :
                public .print_log (public .get_error_info ())
        public .writeFile (OO0O0OOO00O0OO00O .__O00OOOO00OO0OO0OO ,json .dumps (O00000OOO00OO000O ))
    def __O0000OO00OO00O0O0 (OO0000O0OO00O0OOO ,O0O0O00OO0OOOOOOO ):
        ""
        if not OO0000O0OO00O0OOO .__OO000OOO0OO0O00OO ():return public .returnMsg (False ,OO0000O0OO00O0OOO .__O0O00000000OOO0O0 )
        if not os .path .exists (OO0000O0OO00O0OOO .__O00OOOO00OO0OO0OO ):
            public .writeFile (OO0000O0OO00O0OOO .__O00OOOO00OO0OO0OO ,'[]')
        OOOO0000OOOO0OOOO =int (O0O0O00OO0OOOOOOO ['size'])
        OOO000O0OO00O00OO =O0O0O00OO0OOOOOOO .db_name .strip ()
        O0OO0OOOOO00O00OO =json .loads (public .readFile (OO0000O0OO00O0OOO .__O00OOOO00OO0OO0OO ))
        for OO000O0O0O0O000OO in O0OO0OOOOO00O00OO :
            if OO000O0O0O0O000OO ['db_name']==OOO000O0OO00O00OO :
                return public .returnMsg (False ,'Database quota already exists')
        O0OO0OOOOO00O00OO .append ({'db_name':OOO000O0OO00O00OO ,'size':OOOO0000OOOO0OOOO ,'insert_accept':True })
        public .writeFile (OO0000O0OO00O0OOO .__O00OOOO00OO0OO0OO ,json .dumps (O0OO0OOOOO00O00OO ))
        public .WriteLog ('Quota','The quota limit for creating database [{db_name}] is: {size}MB'.format (db_name =OOO000O0OO00O00OO ,size =OOOO0000OOOO0OOOO ))
        OO0000O0OO00O0OOO .mysql_quota_check ()
        return public .returnMsg (True ,'Added successfully')
    def __OO000OOO0OO0O00OO (OOOO00OOOO00O0O00 ):
        import panelPlugin 
        O0OOOOOO0O0000O0O =public .to_dict_obj ({})
        O0OOOOOO0O0000O0O .focre =1 
        O0O0O00O0OO00O000 =panelPlugin .panelPlugin ().get_soft_list (O0OOOOOO0O0000O0O )
        return int (O0O0O00O0OO00O000 ['pro'])>time .time ()
    def modify_mysql_quota (OO00OO0OOOO00O000 ,OOOO00O0OO000OOOO ):
        ""
        if not OO00OO0OOOO00O000 .__OO000OOO0OO0O00OO ():return public .returnMsg (False ,OO00OO0OOOO00O000 .__O0O00000000OOO0O0 )
        if not os .path .exists (OO00OO0OOOO00O000 .__O00OOOO00OO0OO0OO ):
            public .writeFile (OO00OO0OOOO00O000 .__O00OOOO00OO0OO0OO ,'[]')
        if not re .match (r"^\d+$",OOOO00O0OO000OOOO .size ):return public .returnMsg (False ,'Quota size must be an integer!')
        OO0O0OOOO00000OOO =int (OOOO00O0OO000OOOO ['size'])
        OO0OO0OO000O0O00O =OOOO00O0OO000OOOO .db_name .strip ()
        O0OOOO0OOOO0O0000 =json .loads (public .readFile (OO00OO0OOOO00O000 .__O00OOOO00OO0OO0OO ))
        O0O00O0O000OOO0O0 =False 
        for OO00O0000O0OOOOO0 in O0OOOO0OOOO0O0000 :
            if OO00O0000O0OOOOO0 ['db_name']==OO0OO0OO000O0O00O :
                OO00O0000O0OOOOO0 ['size']=OO0O0OOOO00000OOO 
                O0O00O0O000OOO0O0 =True 
                break 
        if O0O00O0O000OOO0O0 :
            public .writeFile (OO00OO0OOOO00O000 .__O00OOOO00OO0OO0OO ,json .dumps (O0OOOO0OOOO0O0000 ))
            public .WriteLog ('Quota','Modify the quota limit of database [{db_name}] to: {size}MB'.format (db_name =OO0OO0OO000O0O00O ,size =OO0O0OOOO00000OOO ))
            OO00OO0OOOO00O000 .mysql_quota_check ()
            return public .returnMsg (True ,'Successfully modified')
        return OO00OO0OOOO00O000 .__O0000OO00OO00O0O0 (OOOO00O0OO000OOOO )
    def __O0OOOO00O00000OOO (O0OO0O0O00O0OO00O ,O0O0O0O0O000O0OOO ):
        ""
        O0OOO0OO0O0000O00 =[]
        OO0000OO0OO00O0O0 =public .ExecShell ("{xfs_quota} -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format (xfs_quota =O0OO0O0O00O0OO00O .xfs_quota ,mountpoint =O0O0O0O0O000O0OOO ))[0 ]
        if not OO0000OO0OO00O0O0 :return O0OOO0OO0O0000O00 
        for O0OO0O00OO0O0OO0O in OO0000OO0OO00O0O0 .split ('\n'):
            if O0OO0O00OO0O0OO0O :O0OOO0OO0O0000O00 .append (int (O0OO0O00OO0O0OO0O .split ('#')[-1 ]))
        return O0OOO0OO0O0000O00 
    def __OO00O000OOOOOOO00 (O0OOO0O00OOOO0OOO ,OO0000O0OOOOOOO0O ,OOO0000OO0O0000OO ):
        ""
        O00O00OO0O000O000 =1001 
        if not OO0000O0OOOOOOO0O :return O00O00OO0O000O000 
        O00O00OO0O000O000 =OO0000O0OOOOOOO0O [-1 ]['id']+1 
        O0OO00OO00O00O000 =sorted (O0OOO0O00OOOO0OOO .__O0OOOO00O00000OOO (OOO0000OO0O0000OO ))
        if O0OO00OO00O00O000 :
            if O0OO00OO00O00O000 [-1 ]>O00O00OO0O000O000 :
                O00O00OO0O000O000 =O0OO00OO00O00O000 [-1 ]+1 
        return O00O00OO0O000O000 
    def __OOOO0O000OOOO00O0 (OO0OO00O0O0000O0O ,O000O0OOOO0OOO00O ):
        ""
        if not OO0OO00O0O0000O0O .__OO000OOO0OO0O00OO ():return public .returnMsg (False ,OO0OO00O0O0000O0O .__O0O00000000OOO0O0 )
        OOOO000000O00OO00 =O000O0OOOO0OOO00O .path .strip ()
        OO000OOO0000OO00O =int (O000O0OOOO0OOO00O .size )
        if not os .path .exists (OOOO000000O00OO00 ):return public .returnMsg (False ,'The specified directory does not exist')
        if os .path .isfile (OOOO000000O00OO00 ):return public .returnMsg (False ,'this is not a valid directory!')
        if os .path .islink (OOOO000000O00OO00 ):return public .returnMsg (False ,'The specified directory is a soft link!')
        OOOOO000OO0000OOO =OO0OO00O0O0000O0O .get_quota_path_list ()
        for O00O0OOOO0O00O000 in OOOOO000OO0000OOO :
            if O00O0OOOO0O00O000 ['path']==OOOO000000O00OO00 :return public .returnMsg (False ,'The specified directory has already set a quota!')
        OO000O0OO0000OO00 =OO0OO00O0O0000O0O .__O000O0O0000OOOOOO (OOOO000000O00OO00 )
        if OO000O0OO0000OO00 ==-3 :return public .returnMsg (False ,'The partition where the specified directory is located is not an XFS partition and does not support directory quotas!')
        if OO000O0OO0000OO00 ==-2 :return public .returnMsg (False ,'this is not a valid directory!')
        if OO000O0OO0000OO00 ==-1 :return public .returnMsg (False ,'The specified directory does not exist!')
        if OO000OOO0000OO00O >OO000O0OO0000OO00 :return public .returnMsg (False ,'Insufficient quota capacity available for the specified disk!')
        OOO0O0O0O0O000O0O =OO0OO00O0O0000O0O .__O000000O0O0000OOO (OOOO000000O00OO00 )
        if not OOO0O0O0O0O000O0O :return public .returnMsg (False ,'The specified directory is not in the xfs disk partition!')
        if isinstance (OOO0O0O0O0O000O0O ,tuple ):return public .returnMsg (False ,'The directory quota function is not enabled for this xfs partition, please increase the [prjquota] parameter when mounting the partition<p>/etc/fstab File configuration example：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>Note: You need to remount the partition or reboot the server to take effect</p><br>The setup is completed and the error still occurs, please refer to<br><a class="btlink"  target ="_blank" href="https://forum.aapanel.com/d/12700-how-to-enable-disk-quota-for-root-directory">How to enable disk quota for root directory</a>'.format (mountpoint =OOO0O0O0O0O000O0O [1 ],path =OOO0O0O0O0O000O0O [0 ]))
        O0000OO000OO00O0O =OO0OO00O0O0000O0O .__OO00O000OOOOOOO00 (OOOOO000OO0000OOO ,OOO0O0O0O0O000O0O )
        OO0O0O0O0OOOOO00O =public .ExecShell ("{xfs_quota} -x -c 'project -s -p {path} {quota_id}'".format (path =OOOO000000O00OO00 ,quota_id =O0000OO000OO00O0O ,xfs_quota =OO0OO00O0O0000O0O .xfs_quota ))
        if OO0O0O0O0OOOOO00O [1 ]:return public .returnMsg (False ,OO0O0O0O0OOOOO00O [1 ])
        OO0O0O0O0OOOOO00O =public .ExecShell ("{xfs_quota} -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O0000OO000OO00O0O ,size =OO000OOO0000OO00O ,mountpoint =OOO0O0O0O0O000O0O ,xfs_quota =OO0OO00O0O0000O0O .xfs_quota ))
        if OO0O0O0O0OOOOO00O [1 ]:return public .returnMsg (False ,OO0O0O0O0OOOOO00O [1 ])
        OOOOO000OO0000OOO .append ({'path':O000O0OOOO0OOO00O .path ,'size':OO000OOO0000OO00O ,'id':O0000OO000OO00O0O })
        public .writeFile (OO0OO00O0O0000O0O .__O0O000000OO000000 ,json .dumps (OOOOO000OO0000OOO ))
        public .WriteLog ('Quota','The quota limit for creating directory [{path}] is: {size}MB'.format (path =OOOO000000O00OO00 ,size =OO000OOO0000OO00O ))
        return public .returnMsg (True ,'Added successfully')
    def modify_path_quota (O0O0OOOOO0OOO0OOO ,OO0O0000000OO0OO0 ):
        ""
        if not O0O0OOOOO0OOO0OOO .__OO000OOO0OO0O00OO ():return public .returnMsg (False ,O0O0OOOOO0OOO0OOO .__O0O00000000OOO0O0 )
        O00O0O00OOO0O0O0O =OO0O0000000OO0OO0 .path .strip ()
        if not re .match (r"^\d+$",OO0O0000000OO0OO0 .size ):return public .returnMsg (False ,'Quota size must be an integer!')
        O0O00O0OOO0O0O0OO =int (OO0O0000000OO0OO0 .size )
        if not os .path .exists (O00O0O00OOO0O0O0O ):return public .returnMsg (False ,'The specified directory does not exist')
        if os .path .isfile (O00O0O00OOO0O0O0O ):return public .returnMsg (False ,'This is not a valid directory!')
        if os .path .islink (O00O0O00OOO0O0O0O ):return public .returnMsg (False ,'The specified directory is a soft link!')
        OO0O00O00OO0000OO =O0O0OOOOO0OOO0OOO .get_quota_path_list ()
        OOOO0OO0OOOOO0OOO =0 
        for OOO00000OOOOO0OOO in OO0O00O00OO0000OO :
            if OOO00000OOOOO0OOO ['path']==O00O0O00OOO0O0O0O :
                OOOO0OO0OOOOO0OOO =OOO00000OOOOO0OOO ['id']
                break 
        if not OOOO0OO0OOOOO0OOO :return O0O0OOOOO0OOO0OOO .__OOOO0O000OOOO00O0 (OO0O0000000OO0OO0 )
        O0O0O00OOOOOO00O0 =O0O0OOOOO0OOO0OOO .__O000O0O0000OOOOOO (O00O0O00OOO0O0O0O )
        if O0O0O00OOOOOO00O0 ==-3 :return public .returnMsg (False ,'The partition where the specified directory is located is not an XFS partition, and directory quotas are not supported!')
        if O0O0O00OOOOOO00O0 ==-2 :return public .returnMsg (False ,'This is not a valid directory!')
        if O0O0O00OOOOOO00O0 ==-1 :return public .returnMsg (False ,'The specified directory does not exist!')
        if O0O00O0OOO0O0O0OO >O0O0O00OOOOOO00O0 :return public .returnMsg (False ,'Insufficient quota capacity available for the specified disk!')
        OOO0OO0O0000O0OO0 =O0O0OOOOO0OOO0OOO .__O000000O0O0000OOO (O00O0O00OOO0O0O0O )
        if not OOO0OO0O0000O0OO0 :return public .returnMsg (False ,'The specified directory is not in the xfs disk partition!')
        if isinstance (OOO0OO0O0000O0OO0 ,tuple ):return public .returnMsg (False ,'The directory quota function is not enabled for this xfs partition, please increase the [prjquota] parameter when mounting the partition<p>/etc/fstab File configuration example：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>Note: After the configuration is complete, you need to remount the partition or restart the server to take effect</p>'.format (mountpoint =OOO0OO0O0000O0OO0 [1 ],path =OOO0OO0O0000O0OO0 [0 ]))
        OO00O0OOO00OOOO0O =public .ExecShell ("{xfs_quota} -x -c 'project -s -p {path} {quota_id}'".format (path =O00O0O00OOO0O0O0O ,quota_id =OOOO0OO0OOOOO0OOO ,xfs_quota =O0O0OOOOO0OOO0OOO .xfs_quota ))
        if OO00O0OOO00OOOO0O [1 ]:return public .returnMsg (False ,OO00O0OOO00OOOO0O [1 ])
        OO00O0OOO00OOOO0O =public .ExecShell ("{xfs_quota} -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =OOOO0OO0OOOOO0OOO ,size =O0O00O0OOO0O0O0OO ,mountpoint =OOO0OO0O0000O0OO0 ,xfs_quota =O0O0OOOOO0OOO0OOO .xfs_quota ))
        if OO00O0OOO00OOOO0O [1 ]:return public .returnMsg (False ,OO00O0OOO00OOOO0O [1 ])
        for OOO00000OOOOO0OOO in OO0O00O00OO0000OO :
            if OOO00000OOOOO0OOO ['path']==O00O0O00OOO0O0O0O :
                OOO00000OOOOO0OOO ['size']=O0O00O0OOO0O0O0OO 
                break 
        public .writeFile (O0O0OOOOO0OOO0OOO .__O0O000000OO000000 ,json .dumps (OO0O00O00OO0000OO ))
        public .WriteLog ('Quota','Modify the quota limit of directory [{path}] to:{size}MB'.format (path =O00O0O00OOO0O0O0O ,size =O0O00O0OOO0O0O0OO ))
        return public .returnMsg (True ,'Successfully modified')

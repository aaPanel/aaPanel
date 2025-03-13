#coding: utf-8
#  + -------------------------------------------------------------------
# | aaPanel
#  + -------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
#  + -------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
#  + -------------------------------------------------------------------
import public,db,re,os,firewalls
try:
    from BTPanel import session
except: pass
class ftp:
    __runPath = None
    
    def __init__(self):
        self.__runPath = '/www/server/pure-ftpd/bin'
        
    
    #添加FTP
    def AddUser(self,get):
        try:
            if not os.path.exists('/www/server/pure-ftpd/sbin/pure-ftpd'): return public.return_msg_gettext(False, public.lang("Please install the Pure-FTPd service in the software store first."))
            import files,time
            fileObj=files.files()
            if get['ftp_username'].strip().find(' ') != -1: return public.returnMsg(False, public.lang("Username cannot contain spaces"))
            if re.search(r"\W+",get['ftp_username']): return {'status':False,'code':501,'msg':public.lang("Username is illegal, special characters are NOT allowed!")}
            if len(get['ftp_username']) < 3: return {'status':False,'code':501,'msg':public.lang("Username is illegal, cannot be less than 3 characters!")}
            if not fileObj.CheckDir(get['path']): return {'status':False,'code':501,'msg':public.lang("System critical directory cannot be used as FTP directory!")}
            if public.M('ftps').where('name=?',(get.ftp_username.strip(),)).count(): return public.return_msg_gettext(False,'User [{}] exists!',(get.ftp_username,))
            username = get['ftp_username'].strip()
            if re.search("[\\/\\\\:\\*\\?\"\'\\<\\>\\|]+",username):
                return public.return_msg_gettext(False, public.lang("Name cannot contain /\\:*?\"<>| symbol"))
            password = get['ftp_password'].strip()
            if len(password) < 6: return public.return_msg_gettext(False, 'Password must be at least [{}] characters',("6",))
            get.path = get['path'].replace(' ','')
            get.path = get.path.replace("\\", "/")
            fileObj.CreateDir(get)
            public.ExecShell('chown www.www ' + get.path)
            public.ExecShell(self.__runPath + '/pure-pw useradd "' + username + '" -u www -d ' + get.path + '<<EOF \n' + password + '\n' + password + '\nEOF')
            self.FtpReload()
            ps = public.xssencode2(get['ps'])
            if get['ps']=='': ps= public.lang("Edit notes");
            addtime=time.strftime('%Y-%m-%d %X',time.localtime())
            
            pid = 0
            if hasattr(get,'pid'): pid = get.pid
            public.M('ftps').add('pid,name,password,path,status,ps,addtime',(pid,username,password,get.path,1,ps,addtime))
            public.write_log_gettext('FTP manager', 'Successfully added FTP user [{}]!',(username,))
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except Exception as ex:
            public.write_log_gettext('FTP manager', 'Failed to add FTP user[{}]! => {}',(username,str(ex)))
            return public.return_msg_gettext(False, public.lang("Failed to add"))
    
    #删除用户
    def DeleteUser(self,get):
        try:
            username = get['username']
            id = get['id']
            if public.M('ftps').where("id=? and name=?", (id,username, )).count()==0:
                return public.return_msg_gettext(False, public.lang("Failed to delete"))
            public.ExecShell(self.__runPath + '/pure-pw userdel "' + username + '"')
            self.FtpReload()
            public.M('ftps').where("id=?",(id,)).delete()
            public.write_log_gettext('FTP manager', 'Successfully deleted FTP user[{}]!',(username,))
            return public.return_msg_gettext(True, public.lang("Successfully deleted"))
        except Exception as ex:
            public.write_log_gettext('FTP manager', 'Faided to delete FTP user[{}]! => {}',(username,str(ex)))
            return public.return_msg_gettext(False, public.lang("Failed to delete"))
    
    
    #修改用户密码
    def SetUserPassword(self,get):
        try:
            id = get['id']
            username = get['ftp_username'].strip()
            password = get['new_password'].strip()
            if public.M('ftps').where("id=? and name=?", (id,username, )).count()==0:
                return public.return_msg_gettext(False, public.lang("Failed to delete"))
            if len(password) < 6: return public.return_msg_gettext(False,'Password must be at least [{}] characters',("6",))
            public.ExecShell(self.__runPath + '/pure-pw passwd "' + username + '"<<EOF \n' + password + '\n' + password + '\nEOF')
            self.FtpReload()
            public.M('ftps').where("id=?",(id,)).setField('password',password)
            public.write_log_gettext('FTP manager', 'Successfully changed password for FTP user[{}]!',(username,))
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except Exception as ex:
            public.write_log_gettext('FTP manager', 'Failed to change password FTP user[{}]! => {}',(username,str(ex)))
            return public.return_msg_gettext(False, public.lang("Failed to modify"))
    
    
    #设置用户状态
    def SetStatus(self,get):
        msg = public.lang("Turn off");
        if get.status != '0': msg = public.lang("Turn on");
        try:
            id = get['id']
            username = get['username']
            status = get['status']
            if public.M('ftps').where("id=? and name=?", (id,username, )).count()==0:
                return public.return_msg_gettext(False, public.lang("Failed to delete"))
            if int(status)==0:
                public.ExecShell(self.__runPath + '/pure-pw usermod "' + username + '" -r 1')
            else:
                public.ExecShell(self.__runPath + '/pure-pw usermod "' + username + "\" -r ''")
            self.FtpReload()
            public.M('ftps').where("id=?",(id,)).setField('status',status)
            public.write_log_gettext('FTP manager','Successfully {} FTP user [{}]!', (msg,username))
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except Exception as ex:
            public.write_log_gettext('FTP manager','Failed to {} FTP user [{}]! => {}', (msg,username,str(ex)))
            return public.return_msg_gettext(False,'{} FTP user failed!',(msg,))
    
    '''
     * 设置FTP端口
     * @param Int _GET['port'] 端口号
     * @return bool
     '''
    def setPort(self,get):
        try:
            port = get['port'].strip()
            if not port: return public.returnMsg(False, public.lang("Please enter an integer for the port"))
            if int(port) < 1 or int(port) > 65535: return public.return_msg_gettext(False, public.lang("Port range is incorrect!"))
            file = '/www/server/pure-ftpd/etc/pure-ftpd.conf'
            conf = public.readFile(file)
            rep = u"\n#?\\s*Bind\\s+[0-9]+\\.[0-9]+\\.[0-9]+\\.+[0-9]+,([0-9]+)"
            #preg_match(rep,conf,tmp)
            conf = re.sub(rep,"\nBind        0.0.0.0," + port,conf)
            public.writeFile(file,conf)
            public.ExecShell('/etc/init.d/pure-ftpd restart')
            public.write_log_gettext('FTP manager', "Successfully modified FTP port to [{}]!",(port,))
            #添加防火墙
            #data = ftpinfo(port=port,ps = 'FTP端口')
            get.port=port
            get.ps = public.lang("FTP port");
            firewalls.firewalls().AddAcceptPort(get)
            session['port']=port
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except Exception as ex:
            public.write_log_gettext('FTP manager', 'Failed to modify FTP port! => {}',(str(ex),))
            return public.return_msg_gettext(False, public.lang("Failed to modify"))
    
    #重载配置
    def FtpReload(self):
        public.ExecShell(self.__runPath + '/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb')

    def get_login_logs(self, get):
        import ftplog
        ftpobj = ftplog.ftplog()
        return ftpobj.get_login_log(get)
    def get_action_logs(self, get):
        import ftplog
        ftpobj = ftplog.ftplog()
        return ftpobj.get_action_log(get)

    def set_ftp_logs(self, get):
        import ftplog
        ftpobj = ftplog.ftplog()
        result = ftpobj.set_ftp_log(get)
        return result

    #修改用户密码
    def set_user_home(self,get):
        """
        change user home
        id: ftp id
        path: the new ftp user home
        ftp_username: ftp username
        migrate: migrate ftp user data to the new home

        """
        try:
            id = get['id']
            path = get['path']
            username = get['ftp_username']
            # get the old path in the panel sqlite db
            old_path = public.M("ftps").where("id=?",(id,)).getField('path')
            # check the auth ftp user if exists
            auth_conf_file = '/www/server/pure-ftpd/etc/pureftpd.passwd'
            auth_conf = public.readFile(auth_conf_file)
            if not auth_conf:
                return public.returnMsg(False, public.lang("FTP account has not been set up"))
            # get the user specified conf
            auth_conf_list = [i for i in auth_conf.split('\n')]
            rep = '^{}:.*'.format(username)
            macth_conf = [i for i in auth_conf_list if re.search(rep,i)]
            if not macth_conf:
                return public.returnMsg(False, public.lang("FTP account has not been set up1"))
            if len(macth_conf) > 1:
                return public.returnMsg(False, public.lang("Matching multiple configurations, this operation has been stopped!"))
            if not os.path.exists(path):
                os.makedirs(path)
                public.ExecShell('chown www.www ' + path)
            # replace the old path
            result = macth_conf[0]
            specified_user_conf = result.replace(old_path,path)
            auth_conf = auth_conf.replace(result,specified_user_conf)
            public.writeFile(auth_conf_file,auth_conf)
            if get.migrate == '1':
                public.ExecShell('cp -rp {}/* {}'.format(old_path,path))
            self.FtpReload()
            public.M('ftps').where("id=?",(id,)).setField('path',path)
            public.write_log_gettext('FTP manager', 'Successfully changed password for FTP user[{}]!',(path,))
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except Exception as ex:
            return public.get_error_info()
            public.write_log_gettext('FTP manager', 'FTP_PASS_ERR',(path,str(ex)))
            return public.returnMsg(False, public.lang("Failed to modify"))
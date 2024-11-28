#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel x5
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2018 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 1249648969@qq.com
# +-------------------------------------------------------------------
import sys,os,public,re,firewalld,time

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

class firewalls:
    __isFirewalld = False
    __isUfw = False
    __Obj = None


    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'): self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__isUfw = True
        public.M('firewall').execute("alter table firewall add ports TEXT;",())
        public.M('firewall').execute("alter table firewall add protocol TEXT;",())
        public.M('firewall').execute("alter table firewall add address_ip TEXT;",())
        public.M('firewall').execute("alter table firewall add types TEXT;",())
        #这里判断的是Centos7 的系统
        if self.__isFirewalld:
            self.__Obj = firewalld.firewalld();
            # 获取列表信息
            self.GetList();
               
    #获取服务端列表
    def GetList(self,get = None):
        try:
            data = {}
            # 获取开放的端口
            data['ports'] = self.__Obj.GetAcceptPortList();
            #当前时间
            #'2018-10-11 14:36:40'
            addtime = time.strftime('%Y-%m-%d %X',time.localtime())
            #
            for i in range(len(data['ports'])):
                #
                tmp = self.CheckDbExists(data['ports'][i]['port'],data['ports'][i]['protocol']);
                # | id | port  | ps  | addtime   | ports | protocol | address_ip | types |
                if not tmp: public.M('firewall').add('port,ps,addtime',(data['ports'][i]['port'],'',addtime))
                          
            data['iplist'] = self.__Obj.GetDropAddressList();
            
            for i in range(len(data['iplist'])):
                try:
                    tmp = self.CheckDbExists(data['iplist'][i]['address']);
                    if not tmp: public.M('firewall').add('port,ps,addtime',(data['iplist'][i]['address'],'',addtime))
                except:
                    return public.get_error_info()

            # 添加到firewalls 数据表中
            data['reject']=self.__Obj.GetrejectLIST()

            
            for i in range(len(data['reject'])):
                try:
                    tmp=self.CheckDbExists2(data['reject'][i]['protocol'],
                                            data['reject'][i]['type'],
                                            data['reject'][i]['port'],
                                            data['reject'][i]['address'])
                    if not tmp:public.M('firewall').add('protocol,types,ports,address_ip,addtime',
                                                         (data['reject'][i]['protocol'],
                                                          data['reject'][i]['type'],
                                                          data['reject'][i]['port'],
                                                          data['reject'][i]['address'],addtime))
                except:
                    return public.get_error_info()
            # 添加允许信息到firewalls 表中
            data['accept'] = self.__Obj.Getacceptlist()
            #return data
            for i in range(len(data['accept'])):
                try:
                    tmp = self.CheckDbExists2(data['accept'][i]['protocol'],
                                              data['accept'][i]['type'],
                                              data['accept'][i]['port'],
                                              data['accept'][i]['address'])
                    if not tmp: public.M('firewall').add('protocol,types,ports,address_ip,addtime',
                                                          (data['accept'][i]['protocol'],
                                                           data['accept'][i]['type'],
                                                           data['accept'][i]['port'],
                                                           data['accept'][i]['address'],addtime))
                except:
                    return public.get_error_info()
            count =  public.M('firewall').count();
            data = {}
            data['page'] = public.get_page(count,int(get.p),12,get.collback)
            data['data'] = public.M('firewall').limit(data['page']['shift'] + ',' + data['page']['row']).order('id desc').select()
            for i in range(len(data['data'])):
                if data['data'][i]['port'].find(':') != -1 or data['data'][i]['port'].find('.') != -1 or data['data'][i]['port'].find('-') != -1:
                        data['data'][i]['status'] = -1;
                else:
                    data['data'][i]['status'] = public.check_port_stat(int(data['data'][i]['port']));

            data['page'] = data['page']['page']
            return data
        except Exception as ex:
            return public.get_error_info()
    
    #检查数据库是否存在
    def CheckDbExists(self,port,type=None):
        data = public.M('firewall').field('id,port,ps,addtime,types').select();
        return data
        for dt in data:
            if dt['port'] == port and dt['type'] == type: return dt;
        return False;

    # 查看frewalls 数据库表中是否存在
    # | id | port  | ps  | addtime   | ports | protocol | address_ip | types |
    def CheckDbExists2(self,protocol,type,port,address):
        data = public.M('firewall').field('protocol,types,ports,address_ip').select()
        for dt in data:
            if dt['ports'] == port and dt['protocol']==protocol and dt['types']==type and dt['address_ip']==address: return dt;
        return False



    #重载防火墙配置
    def FirewallReload(self):
        if self.__isUfw:
            public.ExecShell('/usr/sbin/ufw reload')
            return;
        if self.__isFirewalld:
            public.ExecShell('firewall-cmd --reload')
        else:
            public.ExecShell('/etc/init.d/iptables save')
            public.ExecShell('/etc/init.d/iptables restart')
            
        
    #添加屏蔽IP
    def AddDropAddress(self,get):
        import time
        import re
        rep = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
        if not re.search(rep,get.port): return public.return_msg_gettext(False, public.lang("IP address youve entered is illegal!"));
        address = get.port
        if public.M('firewall').where("port=?",(address,)).count() > 0: return public.return_msg_gettext(False, public.lang("The IP exists in block list, no need to repeat processing!"))
        if self.__isUfw:
            public.ExecShell('ufw deny from ' + address + ' to any');
        else:
            if self.__isFirewalld:
                public.ExecShell('firewall-cmd --permanent --add-rich-rule=\'rule family=ipv4 source address="'+ address +'" drop\'')
                ret=self.__Obj.CheckIpDrop(address)
                if not ret:
                    self.__Obj.AddDropAddress(address)
                    
            else:
                public.ExecShell('iptables -I INPUT -s '+address+' -j DROP')
        
        public.write_log_gettext("Firewall manager", 'Successfully blocked IP [{}]!',(address,))
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        public.M('firewall').add('port,ps,addtime',(address,get.ps,addtime))
        self.FirewallReload()
        return public.return_msg_gettext(True, public.lang("Successfully added"))




    #删除IP屏蔽
    def DelDropAddress(self,get):
        address = get.port
        id = get.id
        if self.__isUfw:
            public.ExecShell('ufw delete deny from ' + address + ' to any');
        else:
            if self.__isFirewalld:
                public.ExecShell('firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="'+ address +'" drop\'')
                ret=self.__Obj.DelDropAddress(address)
                if ret:
                    pass    
            else:
                public.ExecShell('iptables -D INPUT -s '+address+' -j DROP')
        
        public.write_log_gettext("Firewall manager",'Unblocked IP [{}]!',(address,))
        public.M('firewall').where("id=?",(id,)).delete()
        
        self.FirewallReload();
        return public.return_msg_gettext(True, public.lang("Successfully deleted"))
    
    
    #添加放行端口
    def AddAcceptPort(self,get):
        flag=False
        import re
        rep = r"^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep,get.port): return public.return_msg_gettext(False, public.lang("Port range is incorrect!"));
        import time
        port = get.port
        ps = get.ps
        types=get.type
        type_list=['tcp','udp']
        if types not in type_list:return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))
        notudps = ['80', '443', '8888', '888', '39000:40000', '21', '22']
        if port in notudps:flag=True
        #return public.M('firewall').where("port=?", (port,)).count()
        if types=='tcp':
            if flag:
                if public.M('firewall').where("port=?", (port,)).count() > 0: return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))
            else:
                 if public.M('firewall').where("port=? and type='tcp'",(port,)).count() > 0: return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))
        elif types=='udp':
            if flag:
                if public.M('firewall').where("port=?", (port,)).count() > 0: return public.return_msg_gettext( False, 'The port exists, no need to repeat the release!')
            else:
                if public.M('firewall').where("port=? and type='udp'", (port,)).count() > 0: return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))
        else:
            return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))

        if self.__isUfw:
            if port in notudps:
                public.ExecShell('ufw allow ' + port + '/tcp')
            else:
                public.ExecShell('ufw allow ' + port + '/'+type+'');
        else:
            if self.__isFirewalld:
                port = port.replace(':','-')
                if  port in notudps:
                    public.ExecShell('firewall-cmd --permanent --zone=public --add-port=' + port + '/tcp')
                else:
                    public.ExecShell('firewall-cmd --permanent --zone=public --add-port=' + port + '/' + types +'')
            else:
                if  port in notudps:
                    public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport ' + port + ' -j ACCEPT')
                else:
                    public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m ' + types +' --dport ' + port + ' -j ACCEPT' )

        public.write_log_gettext("Firewall manager", 'Successfully accepted port [{}]!',(port,))
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        result = public.M('firewall').add('port,ps,addtime,types',(port,ps,addtime,types))
        #return result
        self.FirewallReload()
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))
    
    
    #删除放行端口
    def DelAcceptPort(self,get):
        port = get.port
        id = get.id
        types=get.type
        type_list = ['tcp', 'udp']
        if not types in type_list: return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))
        try:
            if(port == public.GetHost(True)): return public.return_msg_gettext(False, public.lang("Failed，cannot delete current port of the panel!"))
            if self.__isUfw:
                public.ExecShell('ufw delete allow ' + port + '/' + types+ '');
            else:
                if self.__isFirewalld:
                    public.ExecShell('firewall-cmd --permanent --zone=public --remove-port='+port+'/' + types + '')
                else:
                    public.ExecShell('iptables -D INPUT -p tcp -m state --state NEW -m ' + types +' --dport '+port+' -j ACCEPT')
            public.write_log_gettext("Firewall manager", 'Successfully deleted accepted port [{}] on firewall!',(port,))
            public.M('firewall').where("id=?",(id,)).delete()
            
            self.FirewallReload()
            return public.return_msg_gettext(True, public.lang("Successfully deleted"))
        except:
            return public.return_msg_gettext(False, public.lang("Failed to delete"))



    #设置远程端口状态
    def SetSshStatus(self,get):
        version = public.readFile('/etc/redhat-release')
        if int(get['status'])==1:
            msg = public.lang("SSH service turned off")
            act = 'stop'
        else:
            msg = public.lang("SSH service turned on")
            act = 'start'
        
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act);
        elif version.find(' 7.') != -1:
            public.ExecShell("systemctl "+act+" sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd "+act)
        
        public.write_log_gettext("Firewall manager", msg)
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

        
    
    
    #设置ping
    def SetPing(self,get):
        if get.status == '1':
            get.status = '0';
        else:
            get.status = '1';
        filename = '/etc/sysctl.conf'
        conf = public.readFile(filename)
        if conf.find('net.ipv4.icmp_echo') != -1:
            rep = r"net\.ipv4\.icmp_echo.*"
            conf = re.sub(rep,'net.ipv4.icmp_echo_ignore_all='+get.status,conf)
        else:
            conf += "\nnet.ipv4.icmp_echo_ignore_all="+get.status
            
        
        public.writeFile(filename,conf)
        public.ExecShell('sysctl -p')
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        
    
    
    #改远程端口
    def SetSshPort(self,get):
        #return public.returnMsg(False, public.lang("演示服务器，禁止此操作!"));
        port = get.port
        if int(port) < 22 or int(port) > 65535: return public.return_msg_gettext(False, public.lang("Port range must be between 22 and 65535!"));
        ports = ['21','25','80','443','8080','888','8888'];
        if port in ports: return public.return_msg_gettext(False, public.lang(""));
        
        file = '/etc/ssh/sshd_config'
        conf = public.readFile(file)
        
        rep = "#*Port\\s+([0-9]+)\\s*\n"
        conf = re.sub(rep, "Port "+port+"\n", conf)
        public.writeFile(file,conf)
        
        if self.__isFirewalld:
            self.__Obj.AddAcceptPort(port);
            public.ExecShell('setenforce 0');
            public.ExecShell('sed -i "s#SELINUX=enforcing#SELINUX=disabled#" /etc/selinux/config');
            public.ExecShell("systemctl restart sshd.service")
        elif self.__isUfw:
            public.ExecShell('ufw allow ' + port + '/tcp');
            public.ExecShell("service ssh restart")
        else:
            public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport '+port+' -j ACCEPT')
            public.ExecShell("/etc/init.d/sshd restart")
        
        self.FirewallReload()
        public.M('firewall').where("ps=?",(public.lang("SSH Server"),)).setField('port',port)
        public.write_log_gettext("Firewall manager", "Successfully changed SSH port to [{}]!",(port,))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))
    
    #取SSH信息
    def GetSshInfo(self,get):
        file = '/etc/ssh/sshd_config'
        conf = public.readFile(file)
        rep = "#*Port\\s+([0-9]+)\\s*\n"
        port = re.search(rep,conf).groups(0)[0]
        import system
        panelsys = system.system();
        
        version = panelsys.GetSystemVersion();
        if os.path.exists('/usr/bin/apt-get'):
             status = public.ExecShell("service ssh status | grep -P '(dead|stop)'")
        else:
            if version.find(' 7.') != -1:
                status = public.ExecShell("systemctl status sshd.service | grep 'dead'")
            else:
                status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'")
            
        if len(status[0]) > 3:
            status = False
        else:
            status = True
        isPing = True
        try:
            file = '/etc/sysctl.conf'
            conf = public.readFile(file)
            rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
            tmp = re.search(rep,conf).groups(0)[0]
            if tmp == '1': isPing = False
        except:
            isPing = True
        
        
        
        data = {}
        data['port'] = port
        data['status'] = status
        data['ping'] = isPing
        return data

    # 指定端口 放行IP
    def AddSpecifiesIp(self, get):
        '''
        get 里面 有  protocol type port  address ps   五个参数
        protocol == ['tcp','udp']
        types==['reject','accept'] # 放行和禁止
        port = 端口
        address  地址
        :param get :
        :return:
        '''

           # | ports | protocol | address_ip | types |
        flag = False
        import re
        # 判断端口是否正确
        rep = r"^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep, get.port): return public.return_msg_gettext(False, public.lang("Port range is incorrect! should be between 100-65535"));

        # 判断IP是否正确
        rep2 = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
        if not re.search(rep2, get.address): return public.return_msg_gettext(False, public.lang("IP address is illegal!"));
        import time
        ports = get.port
        ps = get.ps
        types = get.type
        protocol=get.protocol
        address_ip=get.address

        protocol_list = ['tcp', 'udp']
        type_list=['reject','accept']
        # 判断type类型是否正确

        if types not in type_list:return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))
        # 判断protocol 类型是否正确

        if protocol not in protocol_list: return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))

        notudps = ['80', '443', '8888', '888', '39000:40000', '21', '22']
        if ports in notudps: flag = True

        # sql 查询
        #sql="select * from firewall where ports='%s' and address_ip='%s' and protocol='%s' and types='%s';" % (str(ports), str(address_ip), str(protocol), str(types))
        query_result = public.M('firewall').where('ports=? and address_ip=? and protocol=? and types=?',(ports, address_ip, protocol, types)).count()
        # 这里大于0 表示存在
        if query_result > 0 : return public.return_msg_gettext(False, public.lang("The port exists, no need to repeat the release!"))

        if self.__isUfw:
            if type=='accept':
                public.ExecShell('ufw allow proto '+ protocol +' from '+ address_ip+' to any port '+ ports +'')

            else:
                public.ExecShell('ufw deny proto ' + protocol + ' from ' + address_ip + ' to any port ' + ports + '')

        else:
            if self.__isFirewalld:
                port = ports.replace(':', '-')
                self.__Obj.Add_Port_IP(port=ports,address=address_ip,pool=protocol,type=types)
            else:
                if type == 'accept':
                    public.ExecShell('iptables -I INPUT -s '+ address_ip +' -p '+ protocol +' --dport '+ ports +' -j ACCEPT')
                else:
                    public.ExecShell(
                        'iptables -I INPUT -s ' + address_ip + ' -p ' + protocol + ' --dport ' + ports + ' -j DROP')


        public.write_log_gettext("Firewall manager", 'Successfully accepted port [{}]!', (ports,))
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        result = public.M('firewall').add('protocol,types,port,address_ip,ps,addtime', (protocol,types,ports,address_ip,ps,addtime))
        self.FirewallReload()
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    # 删除指定放行端口
    def DelSpecifiesIp(self, get):
        '''
        get 里面 有  protocol type port  address ps   五个参数
        protocol == ['tcp','udp']
        type==['reject','accept'] # 放行和禁止
        port = 端口
        address  地址
        :param get:
        :return:
        '''
        ports = get.port
        types = get.type
        protocol=get.protocol
        address_ip=get.address
        protocol_list = ['tcp', 'udp']
        id = get.id
        if protocol not in protocol_list: return public.return_msg_gettext(False, public.lang("Specified protocol does NOT exist!"))
        if self.__isUfw:
            if type=='accept':
                public.ExecShell('ufw delete allow proto ' + protocol + ' from ' + address_ip + ' to any port ' + ports + '')
            else:
                public.ExecShell('ufw delete deny proto ' + protocol + ' from ' + address_ip + ' to any port ' + ports + '')
        else:
            if self.__isFirewalld:
                self.__Obj.Del_Port_IP(port=ports,address=address_ip,pool=protocol,type=types)

            else:
                if type == 'accept':
                    public.ExecShell('iptables -D INPUT -s ' + address_ip + ' -p ' + protocol + ' --dport ' + ports + ' -j ACCEPT')
                else:
                    public.ExecShell('iptables -D INPUT -s ' + address_ip + ' -p ' + protocol + ' --dport ' + ports + ' -j DROP')
        public.write_log_gettext("Firewall manager", 'FIREWALL_DROP_PORT', (ports,))
        public.M('firewall').where("id=?", (id,)).delete()

        self.FirewallReload()
        return public.return_msg_gettext(True, public.lang("Successfully deleted"))



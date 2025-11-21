#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# node.js模型
#------------------------------
import os,sys,re,json,shutil,psutil,time
from urllib.parse import urlparse

from projectModelV2.base import projectBase
import public
from public.validate import Param
try:
    from BTPanel import cache
except:
    pass

class main(projectBase):
    _panel_path = public.get_panel_path()
    _nodejs_plugin_path = public.get_plugin_path('nodejs')
    _nodejs_path = '{}/nodejs'.format(public.get_setup_path())
    _log_name = 'Project management'
    _npm_exec_log = '{}/logs/npm-exec.log'.format(_panel_path)
    _node_pid_path = '{}/vhost/pids'.format(_nodejs_path)
    _node_logs_path = '{}/vhost/logs'.format(_nodejs_path)
    _node_run_scripts = '{}/vhost/scripts'.format(_nodejs_path)
    _pids = None
    _vhost_path = '{}/vhost'.format(_panel_path)
    _www_home = '/home/www'



    def __init__(self):
        if not os.path.exists(self._node_run_scripts):
            os.makedirs(self._node_run_scripts,493)

        if not os.path.exists(self._node_pid_path):
            os.makedirs(self._node_pid_path,493)

        if not os.path.exists(self._node_logs_path):
            os.makedirs(self._node_logs_path,493)
        
        if not os.path.exists(self._www_home):
            os.makedirs(self._www_home,493)
            public.set_own(self._www_home,'www')


    def get_exec_logs(self,get):
        '''
            @name 获取执行日志
            @author hwliang<2021-08-09>
            @param get<dict_obj>
            @return string
        '''
        if not os.path.exists(self._npm_exec_log): return public.returnMsg(False,'NODE_NOT_EXISTS')
        return public.return_message(0,0,public.GetNumLines(self._npm_exec_log,20))
            

    def get_project_list(self,get):
        '''
            @name 获取项目列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('search').String(),
                Param('limit').Integer(),
                Param('p').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 20
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'

        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',('Node',search,search)).count()
            data = public.get_page(count,int(get.p),int(get.limit),get.callback)
            data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',('Node',search,search)).limit(data['shift'] + ',' + data['row']).order(get.order).select()
        else:
            count = public.M('sites').where('project_type=?','Node').count()
            data = public.get_page(count,int(get.p),int(get.limit),get.callback)
            data['data'] = public.M('sites').where('project_type=?','Node').limit(data['shift'] + ',' + data['row']).order(get.order).select()

        for i in range(len(data['data'])):
            data['data'][i] = self.get_project_stat(data['data'][i])
        return public.return_message(0,0,data)


    def get_ssl_end_date(self,project_name):
        '''
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        '''
        import data
        return data.data().get_site_ssl_info('node_{}'.format(project_name))


    
    def is_install_nodejs(self,get):
        '''
            @name 是否安装nodejs版本管理器
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return bool
        '''
        return_message=os.path.exists(self._nodejs_plugin_path)
        return public.return_message(0,0,return_message)
    def _is_install_nodejs(self,get):
        '''
            @name 是否安装nodejs版本管理器
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return bool
        '''
        return os.path.exists(self._nodejs_plugin_path)

    def get_nodejs_version(self,get):
        '''
            @name 获取已安装的nodejs版本
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return list
        '''
        nodejs_list = []
        if not os.path.exists(self._nodejs_path): return public.return_message(0,0,nodejs_list)
        for v in os.listdir(self._nodejs_path):
            if v[0] != 'v' or v.find('.') == -1: continue
            node_path = os.path.join(self._nodejs_path,v)
            node_bin = '{}/bin/node'.format(node_path)
            if not os.path.exists(node_bin):
                if os.path.exists(node_path + '/bin'):
                    public.ExecShell('rm -rf {}'.format(node_path))
                continue
            nodejs_list.append(v)
        return public.return_message(0,0,nodejs_list)



    def get_run_list(self,get):
        '''
            @name 获取node项目启动列表
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_cwd: string<项目目录>
            }
        '''# 校验参数
        try:
            get.validate([
                Param('project_cwd').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_cwd = get.project_cwd.strip()
        if not os.path.exists(project_cwd): 
            return_message=public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        package_file = '{}/package.json'.format(project_cwd)
        if not os.path.exists(package_file): return public.return_message(0,0,{})

        package_content = public.readFile(package_file)
        if not package_content:
            return public.return_message(0, 0, {})

        try:
            package_info = json.loads(package_content)
        except json.JSONDecodeError:
            return public.return_message(0, 0, {})

        # package_info = json.loads(public.readFile(package_file))

        if not 'scripts' in package_info: return public.return_message(0,0,{})
        if not package_info['scripts']: return public.return_message(0,0,{})
        return public.return_message(0,0,package_info['scripts'])


    def get_npm_bin(self,nodejs_version):
        '''
            @name 获取指定node版本的npm路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        npm_path = '{}/{}/bin/npm'.format(self._nodejs_path,nodejs_version)
        if not os.path.exists(npm_path): return False
        return npm_path

    def get_yarn_bin(self,nodejs_version):
        '''
            @name 获取指定node版本的yarn路径
            @author hwliang<2021-08-28>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        yarn_path = '{}/{}/bin/yarn'.format(self._nodejs_path,nodejs_version)
        if not os.path.exists(yarn_path): return False
        return yarn_path


    def get_node_bin(self,nodejs_version):
        '''
            @name 获取指定node版本的node路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        node_path = '{}/{}/bin/node'.format(self._nodejs_path,nodejs_version)
        if not os.path.exists(node_path): return False
        return node_path


    def get_last_env(self,nodejs_version,project_cwd = None):
        '''
            @name 获取前置环境变量
            @author hwliang<2021-08-25>
            @param nodejs_version<string> Node版本
            @return string
        '''
        nodejs_bin_path = '{}/{}/bin'.format(self._nodejs_path,nodejs_version)
        if project_cwd:
            _bin = '{}/node_modules/.bin'.format(project_cwd)
            if os.path.exists(_bin):
                nodejs_bin_path = _bin + ':' + nodejs_bin_path

        last_env = '''PATH={nodejs_bin_path}:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
'''.format(nodejs_bin_path = nodejs_bin_path)
        return last_env


    def install_packages(self,get):
        '''
            @name 安装指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if not os.path.exists(project_find['path']): 
            return_message=public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file): 
            return_message=public.return_error(public.lang('The package.json configuration file was not found in the project directory!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        nodejs_version = project_find['project_config']['nodejs_version']
        
        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        node_modules_path = '{}/node_modules'.format(project_find['path'])

        # 已经安装过的依赖包的情况下，可能存在不同node版本导致的问题，可能需要重新构建依赖包
        rebuild = False
        if os.path.exists(package_lock_file) and os.path.exists(node_modules_path): 
            rebuild = True

        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)
        if not npm_bin and not yarn_bin: 
            return_message=public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        public.writeFile(self._npm_exec_log,"Installing dependencies...\n")
        public.writeFile(self._npm_exec_log,"Downloading dependency package, please wait...\n")
        if yarn_bin:
            if os.path.exists(package_lock_file): 
                os.remove(package_lock_file)
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install >> {} 2>&1".format(project_find['path'],yarn_bin,self._npm_exec_log))
        else:
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install >> {} 2>&1".format(project_find['path'],npm_bin,self._npm_exec_log))
        public.writeFile(self._npm_exec_log,"|-Successify --- Command executed! ---",'a+')
        public.WriteLog(self._log_name, 'Node project: {}, the installation of the dependency package is complete!'.format(project_find['name']))
        if rebuild: # 重新构建已安装模块？
            self.rebuild_project(get.project_name)
        return_message=public.return_data(True,'The dependency package is installed successfully!')
        del return_message['status']
        return public.return_message(0,0, return_message)


    
    def update_packages(self,get):
        '''
            @name 更新指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if not os.path.exists(project_find['path']): 
            return_message=public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file): 
            return_message=public.return_error(public.lang('The package.json configuration file was not found in the project directory!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        if not os.path.exists(package_lock_file): 
            return_message=public.return_error(public.lang('Please install the dependency package first!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        if not npm_bin: 
            return_message=public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        
        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} update &> {}".format(project_find['path'],npm_bin,self._npm_exec_log))
        public.WriteLog(self._log_name, 'Project [{}] update all dependent packages'.format(get.project_name))
        return_message=public.return_data(True,'Dependent package updated successfully!')
        del return_message['status']
        return public.return_message(0,0, return_message)


    def reinstall_packages(self,get):
        '''
            @name 重新安装指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if not os.path.exists(project_find['path']): 
            return_message=public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file): 
            return_message=public.return_error(public.lang('The package.json configuration file was not found in the project directory!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        if os.path.exists(package_lock_file): os.remove(package_lock_file)
        package_path = '{}/node_modules'
        if os.path.exists(package_path): shutil.rmtree(package_path)
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        if not npm_bin: 
            return_message=public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        public.WriteLog(self._log_name,'Node project: {}, all dependent packages have been reinstalled')
        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install &> {}".format(project_find['path'],npm_bin,self._npm_exec_log))
        return_message=public.return_data(True,'Dependent package reinstalled successfully!')
        del return_message['status']
        return public.return_message(0,0, return_message)


    def get_project_modules(self,get):
        '''
            @name 获取指定项目的依赖包列表
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录> 可选
            }
            return list
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('project_cwd').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not 'project_cwd' in get:
            project_find = self.get_project_find(get.project_name)
            if not project_find: 
                return_message=public.return_error(public.lang('The specified item does not exist!'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            project_cwd = project_find['path']
        else:
            project_cwd = get.project_cwd
        mod_path = os.path.join(project_cwd,'node_modules')
        modules = []
        if not os.path.exists(mod_path): return public.return_message(0,0,modules)
        for mod_name in os.listdir(mod_path):
            try:
                mod_pack_file = os.path.join(mod_path,mod_name,'package.json')
                if not os.path.exists(mod_pack_file): continue
                mod_pack_info = json.loads(public.readFile(mod_pack_file))
                pack_info = {
                    "name": mod_name, 
                    "version": mod_pack_info['version'],
                    "description":mod_pack_info['description'],
                    "license": mod_pack_info['license'] if 'license' in mod_pack_info else 'NULL',
                    "homepage": mod_pack_info['homepage']
                    }
                modules.append(pack_info)
            except:
                continue
        return public.return_message(0,0,modules)

    def install_module(self,get):
        '''
            @name 安装指定模块
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_cwd = project_find['path']


        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd,mod_name)
        if os.path.exists(filename): 
            return_message=public.return_error(public.lang('The specified module has been installed!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)

        if not npm_bin and not yarn_bin:
            return_message=public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if yarn_bin:
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} add {} &> {}".format(project_find['path'],yarn_bin,mod_name,self._npm_exec_log))
        else:
            public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} install {} &> {}".format(project_find['path'],npm_bin,mod_name,self._npm_exec_log))
        if not os.path.exists(filename): 
            return_message=public.return_error(public.lang('Failed to install the specified module!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        public.WriteLog(self._log_name,'Node project {}, {} module installation is complete!'.format(get.project_name,mod_name))
        return_message=public.return_data(True,'Successful installation!')
        del return_message['status']
        return public.return_message(0,0, return_message)

    def uninstall_module(self,get):
        '''
            @name 卸载指定模块
            @author hwliang<2021-04-08>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('mod_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_cwd = project_find['path']

        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd,mod_name)
        if not os.path.exists(filename): 
            return_message=public.return_error(public.lang('The specified module is not installed!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)
        if not npm_bin and not yarn_bin: 
            return_message=public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if yarn_bin:
            result = public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} remove {}".format(project_find['path'],yarn_bin,mod_name))
        else:
            result = public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} uninstall {}".format(project_find['path'],npm_bin,mod_name))
        if os.path.exists(filename): 
            result = "\n".join(result)
            if result.find('looking for funding') != -1:
                return_message=public.return_error(public.lang("This module is dependent on other installed modules and cannot be uninstalled!"))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            return_message=public.return_error(public.lang("Unable to uninstall this module!"))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        public.WriteLog(self._log_name,'Node project {}, {} module uninstallation completed!'.format(get.project_name,mod_name))
        return_message=public.return_data(True,'Module unloaded successfully!')
        del return_message['status']
        return public.return_message(0,0, return_message)


    def upgrade_module(self,get):
        '''
            @name 更新指定模块
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('mod_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_cwd = project_find['path']

        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd,mod_name)
        if not os.path.exists(filename): 
            return_message=public.return_error(public.lang('The specified module is not installed!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)

        if not npm_bin: 
            return_message=public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} update {} &> {}".format(project_find['path'],npm_bin,mod_name,self._npm_exec_log))
        public.WriteLog(self._log_name,'Node project {}, {} module update completed!'.format(get.project_name,mod_name))
        return_message=public.return_data(True,'Module updated successfully!')
        del return_message['status']
        return public.return_message(0,0, return_message)
        

    def create_project(self,get):
        '''
            @name 创建新的项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录>
                project_script: string<项目脚本>
                project_ps: string<项目备注信息>
                bind_extranet: int<是否绑定外网> 1:是 0:否
                domains: list<域名列表> ["domain1:80","domain2:80"]  // 在bind_extranet=1时，需要填写
                is_power_on: int<是否开机启动> 1:是 0:否
                run_user: string<运行用户>
                max_memory_limit: int<最大内存限制> // 超出此值项目将被强制重启
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_cwd').String(),
                Param('project_name').String(),
                Param('project_script').String(),
                Param('port').String(),
                Param('run_user').String(),
                Param('nodejs_version').String(),
                Param('project_ps').String(),
                # Param('domains').List(),
                Param('project_env').String(),
                Param('bind_extranet').Integer(),
                Param('is_power_on').Integer(),
                Param('max_memory_limit').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not isinstance(get,public.dict_obj): 
            return_message=public.return_error(public.lang('The parameter type is wrong, need dict obj object'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if not self._is_install_nodejs(get):
            return_message=public.return_error(public.lang('Please install nodejs version manager first'))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        project_name = get.project_name.strip()
        if not re.match(r"^\w+$",project_name): 
            return_message=public.return_error(public.lang('The project name format is incorrect and supports letters, numbers, underscores, and expressions: ^[0-9A-Za-z_]$'))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        if public.M('sites').where('name=?',(get.project_name,)).count():
            return_message=public.return_error('The specified project name already exists: {}'.format(get.project_name))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        get.project_cwd = get.project_cwd.strip()
        if not os.path.exists(get.project_cwd):
            return_message=public.return_error('The project directory does not exist: {}'.format(get.project_cwd))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        
        # 端口占用检测
        if self.check_port_is_used(get.get('port/port')): 
            return_message=public.return_error('This port is already occupied, please modify your project port, port: {}'.format(get.port))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        
        domains = []
        if int(get.bind_extranet) == 1:
            domains = get.domains
            if not public.is_apache_nginx(): 
                return_message=public.return_error(public.lang('Please install Nginx or Apache first'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
        for domain in domains:
            domain_arr = domain.split(':')
            if public.M('domain').where('name=?',domain_arr[0]).count():
                return_message=public.return_error('Domain name already exists: {}'.format(domain))
                del return_message['status']
                return public.return_message(-1,0, return_message)
        pdata = {
            'name': get.project_name,
            'path': get.project_cwd,
            'ps': get.project_ps,
            'status':1,
            'type_id':0,
            'project_type': 'Node',
            'project_config': json.dumps(
                {
                    'project_name': get.project_name,
                    'project_cwd': get.project_cwd,
                    'project_script': get.project_script,
                    'bind_extranet': int(get.bind_extranet),
                    'domains': [],
                    'is_power_on': get.is_power_on,
                    'run_user': get.run_user,
                    'max_memory_limit': get.max_memory_limit,
                    'nodejs_version': get.nodejs_version,
                    'port': int(get.port)
                }
            ),
            'addtime': public.getDate()
        }

        project_id = public.M('sites').insert(pdata)
        if int(get.bind_extranet) == 1:
            format_domains = []
            for domain in domains:
                if domain.find(':') == -1: domain += ':80'
                format_domains.append(domain)
            get.domains = format_domains
            self.project_add_domain(get)
        self.set_config(get.project_name)
        public.WriteLog(self._log_name,'Add Node.js project {}'.format(get.project_name))
        self.install_packages(get)
        self.start_project(get)
        return_message=public.return_data(True,'Added project successfully',project_id)
        del return_message['status']
        return public.return_message(0,0, return_message)
        
    def modify_project(self,get):
        '''
            @name 修改指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录>
                project_script: string<项目脚本>
                project_ps: string<项目备注信息>
                is_power_on: int<是否开机启动> 1:是 0:否
                run_user: string<运行用户>
                max_memory_limit: int<最大内存限制> // 超出此值项目将被强制重启
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_cwd').String(),
                Param('project_name').String(),
                Param('project_script').String(),
                Param('port').String(),
                Param('run_user').String(),
                Param('nodejs_version').String(),
                Param('project_ps').String(),
                Param('domains').String(),
                Param('bind_extranet').Integer(),
                Param('is_power_on').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not isinstance(get,public.dict_obj): 
            return_message=public.return_error(public.lang('The parameter type is wrong, need dict obj'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if not self._is_install_nodejs(get):
            return_message=public.return_error(public.lang('Please install nodejs version manager before installing at least one nodejs'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message=public.return_error('Item does not exist: {}'.format(get.project_name))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        if not os.path.exists(get.project_cwd):
            return_message=public.return_error('The project directory does not exist: {}'.format(get.project_cwd))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        rebuild = False
        if hasattr(get,'port'): 
            if int(project_find['project_config']['port']) != int(get.port):
                if self.check_port_is_used(get.get('port/port'),True): 
                    return_message=public.return_error('The port is already occupied, please modify your port, port: {}'.format(get.port))
                    del return_message['status']
                    return public.return_message(-1,0, return_message)
                project_find['project_config']['port'] = int(get.port)
        if hasattr(get,'project_cwd'): project_find['project_config']['project_cwd'] = get.project_cwd
        if hasattr(get,'project_script'): 
            if not get.project_script.strip():
                return_message=public.return_error(public.lang('Start command cannot be empty'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            project_find['project_config']['project_script'] = get.project_script.strip()
        if hasattr(get,'is_power_on'): project_find['project_config']['is_power_on'] = get.is_power_on
        if hasattr(get,'run_user'): project_find['project_config']['run_user'] = get.run_user
        if hasattr(get,'max_memory_limit'): project_find['project_config']['max_memory_limit'] = get.max_memory_limit
        if hasattr(get,'nodejs_version'): 
            if project_find['project_config']['nodejs_version'] != get.nodejs_version:
                rebuild = True
                project_find['project_config']['nodejs_version'] = get.nodejs_version
        pdata = {
            'path': get.project_cwd,
            'ps': get.project_ps,
            'project_config': json.dumps(project_find['project_config'])
        }

        public.M('sites').where('name=?',(get.project_name,)).update(pdata)
        self.set_config(get.project_name)
        public.WriteLog(self._log_name,'Modify Node.js project {}'.format(get.project_name))
        if rebuild:
            self.rebuild_project(get.project_name)
        return_message=public.return_data(True,'Modify the project successfully')
        del return_message['status']
        return public.return_message(0,0, return_message)
 

    def rebuild_project(self,project_name):
        '''
            @name 重新构建指定项目
            @author hwliang<2021-08-26>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)

        public.ExecShell(self.get_last_env(nodejs_version) + "cd {} && {} rebuild >> {} 2>&1".format(project_find['path'],npm_bin,self._npm_exec_log))
        return True


    def remove_project(self,get):
        '''
            @name 删除指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message=public.return_error('The specified item does not exist: {}'.format(get.project_name))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        
        self.stop_project(get)
        self.clear_config(get.project_name)
        public.M('domain').where('pid=?',(project_find['id'],)).delete()
        public.M('sites').where('name=?',(get.project_name,)).delete()

        pid_file = "{}/{}.pid".format(self._node_pid_path,get.project_name)
        if os.path.exists(pid_file): os.remove(pid_file)
        script_file = '{}/{}.sh'.format(self._node_run_scripts,get.project_name)
        if os.path.exists(script_file): os.remove(script_file)
        log_file = '{}/{}.log'.format(self._node_logs_path,get.project_name)
        if os.path.exists(log_file): os.remove(log_file)
        public.WriteLog(self._log_name,'Delete Node.js project {}'.format(get.project_name))
        return_message=public.return_data(True,'Successfully deleted item')
        del return_message['status']
        return public.return_message(0,0, return_message)


    def project_get_domain(self,get):
        '''
            @name 获取指定项目的域名列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''

        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if not project_id:
            return public.return_message(0, 0, [])
        domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
        return public.return_message(0, 0, domains)


    def project_add_domain(self,get):
        '''
            @name 为指定项目添加域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                # Param('domains').List(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_id = project_find['id']
        
        domains = get.domains
        success_list = []
        error_list = []
        for domain in domains:
            domain = domain.strip()
            if not domain: 
                return_message=public.return_error(public.lang('Domain name cannot be empty'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            domain_arr = domain.split(':')
            if len(domain_arr) == 1: 
                domain_arr.append(80)
                domain += ':80'
            if not public.M('domain').where('name=?',(domain_arr[0],)).count():
                public.M('domain').add('name,pid,port,addtime',(domain_arr[0],project_id,domain_arr[1],public.getDate()))
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self._log_name,'Successfully added the domain [{}] to the project [{}]'.format(domain,get.project_name))
                success_list.append(domain)
            else:
                public.WriteLog(self._log_name,'Domain [{}] already exists'.format(domain))
                error_list.append(domain)

        if success_list:
            public.M('sites').where('id=?',(project_id,)).save('project_config',json.dumps(project_find['project_config']))
            self.set_config(get.project_name)
            return_message=public.return_data(True,"[{}] domain names added successfully, [{}] failed!".format(len(success_list),len(error_list)),error_msg=error_list)
            del return_message['status']
            return public.return_message(0,0, return_message)
        return_message=public.return_data(False,"[{}] domain names added successfully, [{}] failed!".format(len(success_list),len(error_list)),error_msg=error_list)
        del return_message['status']
        return public.return_message(-1,0, return_message)


    def project_remove_domain(self,get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('domain').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('The specified item does not exist'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        last_domain = get.domain
        domain_arr = get.domain.split(':')
        if len(domain_arr) == 1: 
            domain_arr.append(80)
            
        project_id = public.M('sites').where('name=?',(get.project_name,)).getField('id')
        if project_find['project_config']['bind_extranet']:
            if len(project_find['project_config']['domains']) == 1: 
                return_message=public.return_error(public.lang('At least one domain name is required for the mapped project'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
        domain_id = public.M('domain').where('name=? AND pid=?',(domain_arr[0],project_id)).getField('id')
        if not domain_id: 
            return_message=public.return_error(public.lang('The specified domain name does not exist'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        public.M('domain').where('id=?',(domain_id,)).delete()

        if get.domain in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain)
        if get.domain+":80" in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain + ":80")

        public.M('sites').where('id=?',(project_id,)).save('project_config',json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name,'From project: [{}], delete domain name [{}]'.format(get.project_name,get.domain))
        self.set_config(get.project_name)
        return_message=public.return_data(True,'Domain name deleted successfully')
        del return_message['status']
        return public.return_message(0,0, return_message)


    def bind_extranet(self,get):
        '''
            @name 绑定外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                # Param('domains').List(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not public.is_apache_nginx(): 
            return_message=public.return_error(public.lang('Please install Nginx or Apache first'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_name = get.project_name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('Item does not exist'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        if not project_find['project_config']['domains']: 
            return_message=public.return_error(public.lang('Please add at least one domain name in the [Domain Management] option'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_find['project_config']['bind_extranet'] = 1
        public.M('sites').where("id=?",(project_find['id'],)).setField('project_config',json.dumps(project_find['project_config']))
        self.set_config(project_name)
        public.WriteLog(self._log_name,'Node project{}, enable mapping'.format(project_name))
        return_message=public.return_data(True,'Enable the mapping successfully')
        del return_message['status']
        return public.return_message(0,0, return_message)

    
    def set_config(self,project_name):
        '''
            @name 设置项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        if not project_find['project_config']: return False
        if not project_find['project_config']['bind_extranet']: return False
        if not project_find['project_config']['domains']: return False
        self.set_nginx_config(project_find)
        if not public.get_multi_webservice_status():
            self.set_apache_config(project_find)
        public.serviceReload()
        return True

    def clear_config(self,project_name):
        '''
            @name 清除项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        self.clear_nginx_config(project_find)
        self.clear_apache_config(project_find)
        public.serviceReload()
        return True

    def clear_apache_config(self,project_find):
        '''
            @name 清除apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/apache/node_{}.conf".format(self._vhost_path,project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True


    def clear_nginx_config(self,project_find):
        '''
            @name 清除nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/nginx/node_{}.conf".format(self._vhost_path,project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path = self._panel_path,project_name = project_name)
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True


    def set_nginx_config(self,project_find):
        '''
            @name 设置Nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        ports = []
        domains = []
        
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports: 
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        listen_ipv6 = public.listen_ipv6()
        listen_ports = ''
        for p in ports:
            listen_ports += "    listen {};\n".format(p)
            if listen_ipv6:
                listen_ports += "    listen [::]:{};\n".format(p)
        listen_ports = listen_ports.strip()

        is_ssl,is_force_ssl = self.exists_nginx_ssl(project_name)
        ssl_config = ''
        if is_ssl:
            listen_ports += "\n    listen 443 ssl;"
            if listen_ipv6: listen_ports += "\n    listen [::]:443 ssl;"
        
            ssl_config = '''ssl_certificate    {vhost_path}/cert/{priject_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{priject_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";
    error_page 497  https://$host$request_uri;'''.format(vhost_path = self._vhost_path,priject_name = project_name)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''
        
        config_file = "{}/nginx/node_{}.conf".format(self._vhost_path,project_name)
        template_file = "{}/template/nginx/node_http.conf".format(self._vhost_path)
        
        config_body = public.readFile(template_file)
        config_body = config_body.format(
            site_path = project_find['path'],
            domains = ' '.join(domains),
            project_name = project_name,
            panel_path = self._panel_path,
            log_path = public.get_logs_path(),
            url = 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
            host = '$host',
            listen_ports = listen_ports,
            ssl_config = ssl_config
        )

        # # 恢复旧的SSL配置
        # ssl_config = self.get_nginx_ssl_config(project_name)
        # if ssl_config:
        #     config_body.replace('#error_page 404/404.html;',ssl_config)
            

        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path = self._panel_path,project_name = project_name)
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,'# Please fill in the URLrewrite or custom NGINX config here\n')
        public.writeFile(config_file,config_body)
        return True

    def get_nginx_ssl_config(self,project_name):
        '''
            @name 获取项目Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return string
        '''
        result = ''
        config_file = "{}/nginx/node_{}".format(self._vhost_path,project_name)
        if not os.path.exists(config_file): 
            return result

        config_body = public.readFile(config_file)
        if not config_body: 
            return result
        if config_body.find('ssl_certificate') == -1:
            return result

        ssl_body = re.search("#SSL-START(.|\n)+#SSL-END",config_body)
        if not ssl_body: return result
        result = ssl_body.group()
        return result

    def exists_nginx_ssl(self,project_name):
        '''
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        '''
        config_file = "{}/nginx/node_{}.conf".format(public.get_vhost_path(),project_name)
        if not os.path.exists(config_file): 
            return False,False

        config_body = public.readFile(config_file)
        if not config_body: 
            return False,False

        is_ssl,is_force_ssl = False,False
        if config_body.find('ssl_certificate') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl,is_force_ssl

    def exists_apache_ssl(self,project_name):
        '''
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        config_file = "{}/apache/node_{}.conf".format(public.get_vhost_path(),project_name)
        if not os.path.exists(config_file): 
            return False,False

        config_body = public.readFile(config_file)
        if not config_body: 
            return False,False

        is_ssl,is_force_ssl = False,False
        if config_body.find('SSLCertificateFile') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl,is_force_ssl

    def set_apache_config(self,project_find):
        '''
            @name 设置Apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']

        # 处理域名和端口
        ports = []
        domains = []
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports: 
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])

        
        config_file = "{}/apache/node_{}.conf".format(self._vhost_path,project_name)
        template_file = "{}/template/apache/node_http.conf".format(self._vhost_path)
        config_body = public.readFile(template_file)
        apache_config_body = ''

        # 旧的配置文件是否配置SSL
        is_ssl,is_force_ssl  = self.exists_apache_ssl(project_name)
        if is_ssl:
            if not 443 in ports: ports.append(443)
        
        from panelSite import panelSite
        s = panelSite()

        # 根据端口列表生成配置
        for p in ports:
            # 生成SSL配置
            ssl_config = ''
            if p == 443 and is_ssl:
                ssl_key_file = "{vhost_path}/cert/{project_name}/privkey.pem".format(project_name = project_name,vhost_path = public.get_vhost_path())
                if not os.path.exists(ssl_key_file): continue # 不存在证书文件则跳过
                ssl_config = '''#SSL
    SSLEngine On
    SSLCertificateFile {vhost_path}/cert/{project_name}/fullchain.pem
    SSLCertificateKeyFile {vhost_path}/cert/{project_name}/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On'''.format(project_name = project_name,vhost_path = public.get_vhost_path())
            else:
                if is_force_ssl:
                    ssl_config = '''#HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''

            # 生成vhost主体配置
            apache_config_body += config_body.format(
                site_path = project_find['path'],
                server_name = '{}.{}'.format(p,project_name),
                domains = ' '.join(domains),
                log_path = public.get_logs_path(),
                server_admin = 'admin@{}'.format(project_name),
                url = 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
                port = p,
                ssl_config = ssl_config,
                project_name = project_name
            )
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if not p in [80]:
                s.apacheAddPort(p)
        
        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project_find['path'])
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,'# Please fill in the URLrewrite rules or custom Apache config here\n')

        # 写配置文件
        public.writeFile(config_file,apache_config_body)

        # 多服务下使apache配置文件失效
        if public.get_multi_webservice_status():
            if os.path.exists(config_file):
                shutil.move(config_file, config_file + '.barduo')

        return True
    

    def unbind_extranet(self,get):
        '''
            @name 解绑外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_name = get.project_name.strip()
        self.clear_config(project_name)
        public.serviceReload()
        project_find = self.get_project_find(project_name)
        project_find['project_config']['bind_extranet'] = 0
        public.M('sites').where("id=?",(project_find['id'],)).setField('project_config',json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name,'Node project {}, disable the mapping'.format(project_name))
        return_message=public.return_data(True,'Disabled successfully')
        del return_message['status']
        return public.return_message(0,0, return_message)


    def get_project_pids(self,get = None,pid = None, without_request = False):
        '''
            @name 获取项目进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        if get: pid = int(get.pid)
        if not self._pids: self._pids = psutil.pids()
        project_pids = []
        
        for i in self._pids:
            try:
                p = psutil.Process(i)
            except: continue
            if p.ppid() == pid:
                if i in project_pids: continue
                if p.name() in ['bash']: continue
                project_pids.append(i)

        other_pids = []
        for i in project_pids:
            other_pids += self.get_project_pids(pid=i)['message']
        if os.path.exists('/proc/{}'.format(pid)):
            project_pids.append(pid)

        all_pids = list(set(project_pids + other_pids))
        if not all_pids:
            all_pids = self.get_other_pids(pid)['message']
        # public.print_log("all_pids -- {}".format(all_pids))
        def convert_to_int(item):
            try:
                return int(item)
            except ValueError:
                return item

        # 将所有元素转换为整数后进行排序
        sorted_pids = sorted(all_pids, key=convert_to_int)

        if without_request:
            return sorted_pids

        return public.return_message(0,0,sorted_pids)

    def get_other_pids(self,pid):
        '''
            @name 获取其他进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        project_name = None
        for pid_name in os.listdir(self._node_pid_path):
            pid_file = '{}/{}'.format(self._node_pid_path,pid_name)
            #s_pid = int(public.readFile(pid_file))
            data = public.readFile(pid_file)
            if isinstance(data,str) and data:
                data = data.strip()
                if not data.isdigit():
                    return public.return_message(0,0,[])
                s_pid = int(data)
            else:
                return public.return_message(0,0,[])
            if pid == s_pid:
                project_name = pid_name[:-4]
                break
        project_find = self.get_project_find(project_name)
        if not project_find: return public.return_message(0,0,[])
        if not self._pids: self._pids = psutil.pids()
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path']:
                    pname = p.name()
                    if pname in ['node','npm','pm2','yarn'] or pname.find('node ') == 0:
                        cmdline = ','.join(p.cmdline())
                        if cmdline.find('God Daemon') != -1:continue
                        env_list = p.environ()
                        if 'name' in env_list:
                            if not env_list['name'] == project_name: continue
                        if 'NODE_PROJECT_NAME' in env_list:
                            if not env_list['NODE_PROJECT_NAME'] == project_name: continue
                        all_pids.append(i)
            except: continue
        return public.return_message(0,0,all_pids)

    def get_project_state_by_cwd(self,project_name):
        '''
            @name 通过cwd获取项目状态
            @author hwliang<2022-01-17>
            @param project_name<string> 项目名称
            @return bool or list
        '''
        project_find = self.get_project_find(project_name)
        self._pids = psutil.pids()
        if not project_find: return []
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path']:
                    pname = p.name()
                    if pname in ['node','npm','pm2','yarn'] or pname.find('node ') == 0:
                        cmdline = ','.join(p.cmdline())
                        if cmdline.find('God Daemon') != -1:continue
                        env_list = p.environ()
                        if 'name' in env_list:
                            if not env_list['name'] == project_name: continue
                        if 'NODE_PROJECT_NAME' in env_list:
                            if not env_list['NODE_PROJECT_NAME'] == project_name: continue
                        all_pids.append(i)
            except: continue
        if all_pids:
            pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
            public.writeFile(pid_file,str(all_pids[0]))
            return all_pids
        return False

    def kill_pids(self,get=None,pids = None):
        '''
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return dict
        '''
        if get: pids = get.pids
        if not pids: 
            return_message=public.return_data(True, 'No process')
            del return_message['status']
            return public.return_message(0,0, return_message)
        pids = sorted(pids,reverse=True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.kill()
            except:
                pass
        return_message=public.return_data(True, 'The process has all ended')
        del return_message['status']
        return public.return_message(0,0, return_message)



    
    def start_project(self,get):
        '''
            @name 启动项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        pid_file = "{}/{}.pid".format(self._node_pid_path,get.project_name)
        if os.path.exists(pid_file):
            self.stop_project(get)

        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('Item does not exist'))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        if not os.path.exists(project_find['path']):
            error_msg = 'Startup failed, Nodejs project {}, running directory {} does not exist!'.format(get.project_name,project_find['path'])
            public.WriteLog(self._log_name,error_msg)
            return_message=public.return_error(error_msg)
            del return_message['status']
            return public.return_message(-1,0, return_message)

        # 是否安装依赖模块？
        package_file = "{}/package.json".format(project_find['path'])
        package_info = {}
        if os.path.exists(package_file):
            node_modules_path = "{}/node_modules".format(project_find['path'])
            if not os.path.exists(node_modules_path):
                return_message=public.return_error(public.lang('Please go to the [Module] and click [One-key install] to install the module dependencies!'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            package_info = json.loads(public.readFile(package_file))
        if not package_info: package_info['scripts'] = {}
        if 'scripts' not in package_info: package_info['scripts'] = {}
        try:
            scripts_keys = package_info['scripts'].keys()
        except:
            scripts_keys = []
                
        
        # 前置准备
        nodejs_version = project_find['project_config']['nodejs_version']
        node_bin = self.get_node_bin(nodejs_version)
        npm_bin = self.get_npm_bin(nodejs_version)
        project_script = project_find['project_config']['project_script'].strip().replace('  ',' ')
        if project_script[:3] == 'pm2': # PM2启动方式处理
            project_script = project_script.replace('pm2 ','pm2 -u {} -n {} '.format(project_find['project_config']['run_user'],get.project_name))
            project_find['project_config']['run_user'] = 'root'
        log_file = "{}/{}.log".format(self._node_logs_path,get.project_name)
        if not project_script: 
            return_message=public.return_error(public.lang('No startup script configured'))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        last_env = self.get_last_env(nodejs_version,project_find['path'])
        
        # 生成启动脚本
        if os.path.exists(project_script):
            start_cmd = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
cd {project_cwd}
nohup {node_bin} {project_script} >> {log_file} 2>&1 & 
echo $! > {pid_file}
'''.format(
    project_cwd = project_find['path'],
    node_bin = node_bin,
    project_script = project_script,
    log_file = log_file,
    pid_file = pid_file,
    last_env = last_env,
    project_name = get.project_name
)
        elif project_script in scripts_keys:
            start_cmd = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
cd {project_cwd}
nohup {npm_bin} run {project_script} >> {log_file} 2>&1 &
echo $! > {pid_file}
'''.format(
    project_cwd = project_find['path'],
    npm_bin = npm_bin,
    project_script = project_script,
    pid_file = pid_file,
    log_file = log_file,
    last_env = last_env,
    project_name = get.project_name
)
        else:
            start_cmd = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
cd {project_cwd}
nohup {project_script} >> {log_file} 2>&1 &
echo $! > {pid_file}
'''.format(
    project_cwd = project_find['path'],
    project_script = project_script,
    pid_file = pid_file,
    log_file = log_file,
    last_env = last_env,
    project_name = get.project_name

)

        script_file = "{}/{}.sh".format(self._node_run_scripts,get.project_name)

        # 写入启动脚本
        public.writeFile(script_file,start_cmd)
        if os.path.exists(pid_file): os.remove(pid_file)

        # 处理前置权限
        public.ExecShell("chown -R {user}:{user} {project_cwd}".format(user=project_find['project_config']['run_user'],project_cwd=project_find['path']))
        public.ExecShell("chown -R www:www {}/vhost".format(self._nodejs_path))
        public.ExecShell("chmod 755 {} {} {}".format(self._nodejs_path,public.get_setup_path(),'/www'))
        public.set_own(script_file,project_find['project_config']['run_user'],project_find['project_config']['run_user'])
        public.set_mode(script_file,755)

        p = public.ExecShell("bash {}".format(script_file),user=project_find['project_config']['run_user'])

        time.sleep(1)
        n = 0
        while n < 5:
            if self.get_project_state_by_cwd(get.project_name): break
            n+=1
        if not os.path.exists(pid_file):
            p = '\n'.join(p)
            public.writeFile(log_file,p,"a+")
            if p.find('[Errno 0]') != -1:
                if os.path.exists('{}/bt_security'.format(public.get_plugin_path())):
                    return_message=public.return_error('The start command was intercepted by [Fort Tower Defense Privilege], please turn off {} user protection'.format(project_find['project_config']['run_user']))
                    del return_message['status']
                    return public.return_message(-1,0, return_message)
                return_message=public.return_error(public.lang('The startup command was intercepted by unknown security software, please check the installation software log'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            return_message=public.return_error('failed to activate<pre>{}</pre>'.format(p))
            del return_message['status']
            return public.return_message(-1,0, return_message)

        # 获取PID
        try:
            pid = int(public.readFile(pid_file))
        except:
            return public.return_error('Startup failed <br>{}'.format(public.GetNumLines(log_file,20)))

        pids = self.get_project_pids(pid=pid, without_request=True)

        if not pids:
            if os.path.exists(pid_file): os.remove(pid_file)
            return_message=public.return_error('failed to activate<br>{}'.format(public.GetNumLines(log_file,20)))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        return_message=public.return_data(True, 'Successfully started', pids)
        del return_message['status']
        return public.return_message(0,0, return_message)
        

    def stop_project(self,get):
        '''
            @name 停止项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: 
            return_message=public.return_error(public.lang('Project does not exist'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_script = project_find['project_config']['project_script'].strip().replace('  ',' ')
        pid_file = "{}/{}.pid".format(self._node_pid_path,get.project_name)
        if project_script.find('pm2 start') != -1: # 处理PM2启动的项目
            nodejs_version = project_find['project_config']['nodejs_version']
            last_env = self.get_last_env(nodejs_version,project_find['path'])
            project_script = project_script.replace('pm2 start','pm2 stop')
            public.ExecShell('''{}
cd {}
{}'''.format(last_env,project_find['path'],project_script))
        else:
            pid_file = "{}/{}.pid".format(self._node_pid_path,get.project_name)
            if not os.path.exists(pid_file): 
                return_message=public.return_error(public.lang('Project did not start'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            data = public.readFile(pid_file)
            if isinstance(data,str) and data:
                pid = int(data)
                pids = self.get_project_pids(pid=pid, without_request=True)
            else:
                return_message=public.return_error(public.lang('Project did not start'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            if not pids: 
                return_message=public.return_error(public.lang('Project did not start'))
                del return_message['status']
                return public.return_message(-1,0, return_message)
            self.kill_pids(pids=pids)
        if os.path.exists(pid_file): os.remove(pid_file)
        time.sleep(0.5)
        pids = self.get_project_state_by_cwd(get.project_name)
        if pids: self.kill_pids(pids=pids)
        return_message=public.return_data(True, 'Stopped successfully')
        del return_message['status']
        return public.return_message(0,0, return_message)

    def restart_project(self,get):
        '''
            @name 重启项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        res = self.stop_project(get)
        if res['status']==-1: return res
        res = self.start_project(get)
        if res['status']==-1: return res
        return_message=public.return_data(True, 'Successful restart')
        del return_message['status']
        return public.return_message(0,0, return_message)

    # xss 防御
    def xsssec(self,text):
        return text.replace('<', '&lt;').replace('>', '&gt;')


    def get_project_log(self,get):
        '''
            @name 获取项目日志
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        log_file = "{}/{}.log".format(self._node_logs_path,get.project_name)
        if not os.path.exists(log_file): 
            return_message=public.return_error(public.lang('Log file does not exist'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        return public.return_message(0,0,self.xsssec(public.GetNumLines(log_file,200)))
    

    def get_project_load_info(self,get = None,project_name = None):
        '''
            @name 获取项目负载信息
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if get: project_name = get.project_name.strip()
        load_info = {}
        pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
        if not os.path.exists(pid_file):
            return public.return_message(0,0,load_info)
        data = public.readFile(pid_file)
        if isinstance(data,str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)['message']
        else:
            return public.return_message(0,0,load_info)
        if not pids:
            return public.return_message(0,0,load_info)
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return public.return_message(0,0,load_info)


    def object_to_dict(self,obj):
        '''
            @name 将对象转换为字典
            @author hwliang<2021-08-09>
            @param obj<object>
            @return dict
        '''
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result
    
    
    def list_to_dict(self,data):
        '''
            @name 将列表转换为字典
            @author hwliang<2021-08-09>
            @param data<list>
            @return dict
        '''
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result


    def get_connects(self,pid):
        '''
            @name 获取进程连接信息
            @author hwliang<2021-08-09>
            @param pid<int>
            @return dict
        '''
        connects = 0
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp): return connects
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:pass
        return connects


    def format_connections(self,connects):
        '''
            @name 获取进程网络连接信息
            @author hwliang<2021-08-09>
            @param connects<pconn>
            @return list
        '''
        result = []
        for i in connects:
            raddr = i.raddr
            if not i.raddr:
                raddr = ('',0)
            laddr = i.laddr
            if not i.laddr:
                laddr = ('',0)
            result.append({
                "fd": i.fd,
                "family": i.family,
                "local_addr": laddr[0],
                "local_port": laddr[1],
                "client_addr": raddr[0],
                "client_rport": raddr[1],
                "status": i.status
            })
        return result


    def get_process_info_by_pid(self,pid):
        '''
            @name 获取进程信息
            @author hwliang<2021-08-12>
            @param pid: int<进程id>
            @return dict
        '''
        process_info = {}
        try:
            if not os.path.exists('/proc/{}'.format(pid)): return process_info
            p = psutil.Process(pid)
            status_ps = {'sleeping':'Sleeping','running':'Running'}
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: return process_info
                p_state = p.status()
                if p_state in status_ps: p_state = status_ps[p_state]
                # process_info['exe'] = p.exe()
                process_info['name'] = p.name()
                process_info['pid'] = pid
                process_info['ppid'] = p.ppid()
                process_info['create_time'] = int(p.create_time())
                process_info['status'] = p_state
                process_info['user'] = p.username()
                process_info['memory_used'] = p_mem.uss
                process_info['cpu_percent'] = self.get_cpu_precent(p)
                process_info['io_write_bytes'],process_info['io_read_bytes'] = self.get_io_speed(p)
                process_info['connections'] = self.format_connections(p.connections())
                process_info['connects'] = self.get_connects(pid)
                process_info['open_files'] = self.list_to_dict(p.open_files())
                process_info['threads'] = p.num_threads()
                process_info['exe'] = ' '.join(p.cmdline())
                return process_info
        except:
            return process_info


    def get_io_speed(self,p):
        '''
            @name 获取磁盘IO速度
            @author hwliang<2021-08-12>
            @param p: Process<进程对像>
            @return list
        '''

        skey = "io_speed_{}".format(p.pid)
        old_pio = cache.get(skey)
        if not hasattr(p,'io_counters'): return 0,0
        pio = p.io_counters()
        if not old_pio:
            cache.set(skey,[pio,time.time()],3600)
            # time.sleep(0.1)
            old_pio = cache.get(skey)
            pio = p.io_counters()
        
        old_write_bytes = old_pio[0].write_bytes
        old_read_bytes = old_pio[0].read_bytes
        old_time = old_pio[1]

        new_time = time.time()
        write_bytes = pio.write_bytes
        read_bytes = pio.read_bytes

        cache.set(skey,[pio,new_time],3600)

        write_speed = int((write_bytes - old_write_bytes) / (new_time - old_time))
        read_speed = int((read_bytes - old_read_bytes) / (new_time - old_time))
        
        return write_speed,read_speed


    


    def get_cpu_precent(self,p):
        '''
            @name 获取进程cpu使用率
            @author hwliang<2021-08-09>
            @param p: Process<进程对像>
            @return dict
        '''
        skey = "cpu_pre_{}".format(p.pid)
        old_cpu_times = cache.get(skey)
        
        process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        if not old_cpu_times:
            cache.set(skey,[process_cpu_time,time.time()],3600)
            # time.sleep(0.1)
            old_cpu_times = cache.get(skey)
            process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        
        old_process_cpu_time = old_cpu_times[0]
        old_time = old_cpu_times[1]
        new_time = time.time()
        cache.set(skey,[process_cpu_time,new_time],3600)
        percent = round(100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(),2)
        return percent

    
    def get_process_cpu_time(self,cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time


    def get_project_run_state(self,get = None,project_name = None):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get: project_name = get.project_name.strip()
        pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
        if not os.path.exists(pid_file):
            return public.return_message(0,0,False)
        data=public.readFile(pid_file)
        if isinstance(data,str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid, without_request=True)
        else:
            return public.return_message(0,0,self.get_project_state_by_cwd(project_name))
        if not pids:
            return self.get_project_state_by_cwd(project_name)
        return public.return_message(0,0,True)

    def _get_project_run_state(self,get = None,project_name = None):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get: project_name = get.project_name.strip()
        pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
        if not os.path.exists(pid_file):
            return False
        data=public.readFile(pid_file)
        if isinstance(data,str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)['message']
        else:
            return self.get_project_state_by_cwd(project_name)

        if not pids:
            return self.get_project_state_by_cwd(project_name)

        return True

    def get_project_find(self,project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?',('Node',project_name)).find()
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info
        

    def get_project_info(self,get):
        '''
            @name 获取指定项目信息
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        project_info = public.M('sites').where('project_type=? AND name=?',('Node',get.project_name)).find()
        if not project_info: 
            return_message=public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1,0, return_message)
        project_info = self.get_project_stat(project_info)
        return public.return_message(0,0, project_info)


    def get_project_stat(self,project_info):
        '''
            @name 获取项目状态信息
            @author hwliang<2021-08-09>
            @param project_info<dict> 项目信息
            @return list
        '''
        project_info['project_config'] = json.loads(project_info['project_config'])
        project_info['run'] = self._get_project_run_state(project_name = project_info['name'])
        # project_info['run'] = True
        project_info['load_info'] = {}
        if project_info['run']:
            project_info['load_info'] = self.get_project_load_info(project_name = project_info['name'])['message']
        project_info['ssl'] = self.get_ssl_end_date(project_name = project_info['name'])
        project_info['listen'] = []
        project_info['listen_ok'] = True
        if project_info['load_info']:
            for pid in project_info['load_info'].keys():
                if not pid:continue
                if not 'connections' in project_info['load_info'][pid]:
                    project_info['load_info'][pid]['connections'] = []
                for conn in project_info['load_info'][pid]['connections']:
                    if not conn['status'] == 'LISTEN': continue
                    if not conn['local_port'] in project_info['listen']:
                        project_info['listen'].append(conn['local_port'])
            if project_info['listen']:
                project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']
        return project_info
            
        

    def get_project_state(self,project_name):
        '''
            @name 获取项目状态
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?',('Node',project_name)).find()
        if not project_info: return False
        return project_info['status']

    def get_project_listen(self,project_name):
        '''
            @name 获取项目监听端口
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        project_config = json.loads(public.M('sites').where('name=?',project_name).getField('project_config'))
        if 'listen_port' in project_config:
            return project_config['listen_port']
        return False


    def set_project_listen(self,get):
        '''
            @name 设置项目监听端口（请设置与实际端口相符的，仅在自动获取不正确时使用）
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                port: int<端口>
            }
            @return dict
        '''
        project_config = json.loads(public.M('sites').where('name=?',get.project_name).getField('project_config'))
        project_config['listen_port'] = get.port
        public.M('sites').where('name=?',get.project_name).save('project_config',json.dumps(project_config))
        public.WriteLog(self._log_name, 'Modify the port of the project ['+get.project_name+'] to ['+get.port+']')
        return_message=public.return_data(True,'Set successfully')
        del return_message['status']
        return public.return_message(0,0, return_message)


    def set_project_nodejs_version(self,get):
        '''
            @name 设置nodejs版本
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''

        project_config = json.loads(public.M('sites').where('name=?',get.project_name).getField('project_config'))
        project_config['nodejs_version'] = get.nodejs_version
        public.M('sites').where('name=?',get.project_name).save('project_config',json.dumps(project_config))
        public.WriteLog(self._log_name, 'Modify the nodejs version of the project ['+get.project_name+'] to ['+get.nodejs_version+']')
        return_message=public.return_data(True,'Set successfully')
        del return_message['status']
        return public.return_message(0,0, return_message)

    def get_project_nodejs_version(self,project_name):
        '''
            @name 获取nodejs版本
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return string
        '''

        project_config = json.loads(public.M('sites').where('name=?',project_name).getField('project_config'))
        if 'nodejs_version' in project_config: return project_config['nodejs_version']
        return False


    def check_port_is_used(self,port,sock=False):
        '''
            @name 检查端口是否被占用
            @author hwliang<2021-08-09>
            @param port: int<端口>
            @return bool
        '''
        if not isinstance(port,int): port = int(port)
        if port == 0: return False
        project_list = public.M('sites').where('status=? AND project_type=?',(1,'Node')).field('name,path,project_config').select()
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if not 'port' in project_config: continue
            if int(project_config['port']) == port: return True
        if sock: return False
        return public.check_tcp('127.0.0.1',port)

    def get_project_run_state_byaotu(self,project_name):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        pid_file = "{}/{}.pid".format(self._node_pid_path,project_name)
        if not os.path.exists(pid_file): return False
        pid = public.readFile(pid_file)
        pids = self.get_project_pids(pid=pid, without_request=True)
        if not pids: return False
        return True

    def auto_run(self):
        '''
            @name 自动启动所有项目
            @author hwliang<2021-08-09>
            @return bool
        '''
        project_list = public.M('sites').where('project_type=?',('Node',)).field('name,path,project_config').select()
        get= public.dict_obj()
        success_count = 0
        error_count = 0
        for project_find in project_list:
            try:
                project_config = json.loads(project_find['project_config'])
                if project_config['is_power_on'] in [0,False,'0',None]: continue
                project_name = project_find['name']
                project_state = self._get_project_run_state(project_name=project_name)
                if not project_state:
                    get.project_name = project_name
                    result = self.start_project(get)['message']
                    if result['status']==-1:
                        error_count += 1
                        error_msg = 'Automatically start Nodej project ['+project_name+'] failed!'
                        public.WriteLog(self._log_name, error_msg)
                        public.print_log(error_msg + ", " + result['error_msg'],'ERROR')
                    else:
                        success_count += 1
                        success_msg = 'Automatically start the Nodej project ['+project_name+'] successfully!'
                        public.WriteLog(self._log_name, success_msg)
                        public.print_log(success_msg,'INFO')
            except:
                error_count += 1
                public.print_log(public.get_error_info(),'ERROR')
        if (success_count + error_count) < 1: return False
        dene_msg = 'A total of {} Nodejs projects need to be started, {} successfully and {} failed'.format(success_count + error_count,success_count,error_count)
        public.WriteLog(self._log_name, dene_msg)
        public.print_log(dene_msg,'INFO')
        return True

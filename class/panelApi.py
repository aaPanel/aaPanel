#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 阿良 <287962566@qq.com>
# +-------------------------------------------------------------------
#
#             ┏┓      ┏┓
#            ┏┛┻━━━━━━┛┻┓
#            ┃                ☃             ┃
#            ┃  ┳┛   ┗┳ ┃
#            ┃     ┻    ┃
#            ┗━┓      ┏━┛
#              ┃      ┗━━━┓
#              ┃  神兽保佑        ┣┓
#              ┃　  永无BUG！   ┏┛
#              ┗┓┓┏━┳┓┏━━━┛
#               ┃┫┫ ┃┫┫
#               ┗┻┛ ┗┻┛
#
#+------------------------------
#| RESTful API控制器
#+------------------------------
import public,os
from json import loads,dumps
class panelApi:
    tokenFile = 'data/token.json'
    
    #获取Token
    def GetToken(self,get):
        if not os.path.exists(self.tokenFile): return public.returnMsg(False,'NOT_TURNON_API')
        if os.path.exists(self.tokenFile): self.CreateToken(get);
        token = loads(public.readFile(self.tokenFile))
        return token;
    
    #设置Token
    def SetToken(self,get):
        if not os.path.exists(self.tokenFile): return public.returnMsg(False,'NOT_TURNON_API')
        token = loads(public.readFile(self.tokenFile))
        
        #设置AK/SK
        if hasattr(get,'access_key'):
            token['access_key'] = get.access_key
            token['secret_key'] = get.secret_key
        
        #设置权限
        if hasattr(get,'rule'):
            token['rule'] = get.rule.split(',')
            
        #设置IP白名单
        if hasattr(get,'address'):
            token['address'] = get.address.split(',')
        
        
        public.writeFile(self.tokenFile,dumps(token))
        public.WriteLog('API','EDIT_API');
        return public.returnMsg(True,'SET_SUCCESS')
    
    #初始化API接口
    def CreateToken(self,get):
        token = {}
        token['access_key'] = public.GetRandomString(24)
        token['secret_key'] = public.GetRandomString(48)
        token['rule'] = []
        token['address'] = []
        token['status'] = False
        public.writeFile(self.tokenFile,dumps(token))
        public.WriteLog('API','TURNON_API')
        return public.returnMsg(True,'INIT_API')
    
    #设置API接口状态
    def SetTokenStatus(self,get):
        if not os.path.exists(self.tokenFile): return public.returnMsg(False,'NOT_TURNON_API')
        token = loads(public.readFile(self.tokenFile))
        if token['status']:
            token['status'] = False
            public.WriteLog('API','SET_API_STATUS',"关闭");
        else:
            token['status'] = True
            public.WriteLog('API','SET_API_STATUS',"开启");
            
        public.writeFile(self.tokenFile,dumps(token))
        return public.returnMsg(True,'SET_SUCCESS')
    
    
    
        
        
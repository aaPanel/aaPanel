#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lotk
# +-------------------------------------------------------------------

import public,os,sys,db,time,json,re
from BTPanel import session,cache,json_header
from flask import request,redirect,g

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64

try:
    from BTPanel import cache, session
except:
    pass

class userRegister:

    def toRegister(self, post):
        try:
            # 参数检测
            if not hasattr(post, 'email') or not hasattr(post, 'password'):
                return public.return_message(-1, 0, public.lang("User email or password cannot be empty!"))
            
            post.email = post.email.strip()
            post.password = post.password.strip()
            # 检测 email
            emailformat = re.compile(r'[a-zA-Z0-9.-_+%]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+')
            if not emailformat.search(post.email):
                return public.return_message(-1, 0, public.lang("Please enter your vaild email"))

            post.email = self.en_code_rsa(post.email)
            post.password = self.en_code_rsa(post.password)

            params = {}
            params['email'] = post.email
            params['password'] = post.password

            env_info = self.fetch_env_info()
            params['environment_info'] = json.dumps(env_info)

            params['install_code'] = env_info['install_code']
        except Exception as e:
            # return public.return_msg_gettext(False, public.lang("error info : {}", e))
            return public.return_message(-1, 0, public.lang("error info : {}", e))


        # 调用官网注册
        try:

            # public.print_log("传参2   {}".format(params))
            # sUrl = 'http://dev.aapanel.com/api/user/register_on_panel'
            # 判断 普通版 or Pro版
            if hasattr(post, 'isPro') and post.isPro:
                sUrl = '{}/pro/api/user/register_on_panel'.format(public.OfficialApiBase())
            else:
                sUrl = '{}/api/user/register_on_panel'.format(public.OfficialApiBase())

            aa = public.httpPost(sUrl, params, headers={
                'X-Forwarded-For': public.GetClientIp(),
            }, timeout=60)
            data = json.loads(aa)


            if not data['success']:
                if data['res'].startswith("[code: 400] Account is exists!"):
                    data['res'] = '[code: 400] Account is exists!'

                return public.return_message(-1, 0, data['res'])
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            return public.return_message(-1, 0, public.lang("error info2 : {}", e))

        return public.return_message(0, 0, public.lang("Register successfully"))

        # #  注册成功调用登录
        # try:
        #     post.isPro = isPro
        #     self.getToken(post)
        #     return public.return_msg_gettext(True, public.lang("Register successfully"))
        # except Exception as e:
        #     return public.return_msg_gettext(False, public.lang("error info6 : {}", e))




    # 绑定登录
    def getToken(self, get):

        rtmp = ""
        data = {}
        data['identification'] = get.email
        data['password'] = get.password
        data['from_panel'] = self.en_code_rsa('1')  # 1 代表从面板登录
        try:
            # APIURL1 = 'http://dev.aapanel.com/api/user/login'
            APIURL1 = '{}/api/user/login'.format(public.OfficialApiBase())
            rtmp = public.httpPost(APIURL1, data)
            result = json.loads(rtmp)
            if get.isPro:
                if result.get('err_no', None) == 2002:
                    return public.return_message(-1, 0, public.lang("The email has not been validated"))

            if result['success']:
                bind = 'data/bind.pl'
                if os.path.exists(bind): os.remove(bind)
                userinfo = result['res']['user_data']
                userinfo['token'] = result['res']['access_token']
                # 用户信息写入文件
                public.writeFile('data/userInfo.json', json.dumps(userinfo))

                session['focre_cloud'] = True
                return public.return_message(0, 0, public.lang("Bind successfully"))

            else:
                return public.return_message(-1, 0, public.lang("Invalid username or email or password! please check and try again!"))
        except Exception as ex:
            bind = 'data/bind.pl'
            if os.path.exists(bind):
                os.remove(bind)
            return public.return_message(-1, 0, '%s<br>%s' % (
                public.lang("Failed to connect server!"), str(rtmp)))


    def get_cpuname(self):
        return public.ExecShell("cat /proc/cpuinfo|grep 'model name'|cut -d : -f2")[0].strip()


    def fetch_env_info(self,):

        # 获取机器码
        try:
            userPath = 'data/userInfo.json'
            if not os.path.exists(userPath):
                s1 = public.get_mac_address() + public.get_hostname()
                s2 = self.get_cpuname()
                serverid = public.md5(s1) + public.md5(s2)
                data1 = {}
                data1['server_id'] = serverid
                public.writeFile(userPath, json.dumps(data1))

            tmp = public.readFile(userPath)
            if len(tmp) < 2:
                tmp = '{}'
            data = json.loads(tmp)

            if not 'server_id' in data:
                s1 = public.get_mac_address() + public.get_hostname()
                s2 = self.get_cpuname()
                serverid = public.md5(s1) + public.md5(s2)
                data['server_id'] = serverid
                public.writeFile(userPath, json.dumps(data))

            server_id = data['server_id']
        except Exception as e:
            return {}

        return {'ip': public.GetLocalIp(),
                'is_ipv6': 0,
                'os': public.get_platform(),
                'mac': public.get_mac_address(),
                'hdid': public.fetch_disk_SN(),
                'ramid': public.get_memory(),
                'cpuid': public.fetch_cpu_ID(),
                'server_name': public.get_hostname(),
                'install_code': server_id
                }


    # RSA 加密
    def en_code_rsa(self, data):
        pk = public.readFile('data/public.key')
        if not pk:
            return False

        pub_k = RSA.importKey(pk)
        cipher = PKCS1_cipher.new(pub_k)
        rsa_text = base64.b64encode(cipher.encrypt(bytes(data.encode("utf8"))))
        return str(rsa_text, encoding='utf-8')


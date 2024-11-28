#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lotk
# | 邮局调用退订接口(免登录)
# +-------------------------------------------------------------------

import public,os,sys,db,time,json,re


try:
    import jwt
except:
    public.ExecShell('btpip install pyjwt')
    import jwt


class mailUnsubscribe:

    postfix_recipient_blacklist = '/etc/postfix/blacklist'
    # 获取 SECRET_KEY
    def get_SECRET_KEY(self):
        path = '/www/server/panel/data/mail/jwt-secret.txt'
        if not os.path.exists(path):
            secretKey = public.GetRandomString(64)
            public.writeFile(path, secretKey)
        secretKey = public.readFile(path)
        return secretKey


    def Unsubscribe(self, get):
        token = get.get('jwt', '')
        if not token:
            return 'There is no token'
        SECRET_KEY = self.get_SECRET_KEY()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            email = payload['email']

            self.submit_recipient_blacklist(email)

            return public.lang("The unsubscribe of email {} is successful", email)
        except jwt.ExpiredSignatureError:
            return public.lang('Operation failed,The token expires')
        except jwt.InvalidTokenError:
            return public.lang('Operation failed,Invalid tokens')
        except Exception as e:
            return False

    # 退订接口调用的提交黑名单
    def submit_recipient_blacklist(self, email):
        if not os.path.exists(self.postfix_recipient_blacklist):
            public.writeFile(self.postfix_recipient_blacklist, '')

        add_email = f"{email} REJECT\n"

        try:
            # 读取现有文件内容
            with open(self.postfix_recipient_blacklist, 'r') as file:
                existing_lines = set(file.readlines())

            # 只在文件中不存在该行时追加
            if add_email not in existing_lines:
                with open(self.postfix_recipient_blacklist, 'a') as file:
                    file.write(add_email)

                # 更新 Postfix 黑名单数据库
                shell_str = 'postmap /etc/postfix/blacklist'
                public.ExecShell(shell_str)
                return public.return_message(0, 0,  public.lang('Add blacklist successfully'))
            # else:
            #     return public.returnMsg(False, 'Email already in blacklist')

        except Exception as e:
            return public.return_message(-1, 0, str(e))

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

    # 获取 SECRET_KEY
    def get_SECRET_KEY(self):
        path = '/www/server/panel/data/mail/jwt-secret.txt'
        if not os.path.exists(path):
            secretKey = public.GetRandomString(64)
            public.writeFile(path, secretKey)
        secretKey = public.readFile(path)
        return secretKey
    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/postfixadmin.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)
    def M3(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/mail_unsubscribe.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    def Unsubscribe(self, get):
        token = get.get('jwt', '')
        if not token:
            # return 'There is no token'
            return public.returnJson(False, public.lang("There is no token"))
        SECRET_KEY = self.get_SECRET_KEY()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            email = payload['email']
            # etypename = payload['etypename']  # 邮件类型名

            # 优先取用户设置的退订
            untype = get.get('id', '')
            if not untype:
                # 兼容旧退订 邮件类型id
                etypes = payload.get('etypes', '')
                if not etypes:
                    etypes = payload.get('etype', '')
            else:
                etypes = untype


            # 任务主题  发件时间 todo
            subject = payload.get('subject', '')
            send_time = payload.get('send_time', 0)

            task_id = payload.get('task_id', 0)  # 群发任务

            args = public.dict_obj()
            args.email = email
            args.etypes = etypes
            args.task_id = task_id
            args.subject = subject
            args.send_time = send_time


            self.submit_recipient_blacklist(args)

            # return public.lang("The unsubscribe of email {} is successful", email)
            return {"status": True, "msg": public.lang("The unsubscribe of email {} is successful", email)}
        except jwt.ExpiredSignatureError:
            # return public.lang('Operation failed,The token expires')
            return {"status": False, "msg": public.lang('Operation failed,The token expires')}
        except jwt.InvalidTokenError:
            # return public.lang('Operation failed,Invalid tokens')
            # return abort(404)

            return {"status": False, "msg": public.lang('Operation failed,Invalid tokens')}
        except Exception as e:
            return {"status": False, "msg":  f"error: {e}"}

    # 订阅调用  获取类型和邮箱  判断邮箱可用?(邮箱校验 校验后插入)  可用插入数据库   (邮箱校验和邮箱发送营销邮件)
    def Subscribe(self, get):
        etype = get.get('etype', '')
        public.print_log('etype   {}'.format(etype))

        email = get.get('email', '')
        public.print_log('email   {}'.format(email))

        # todo 验证邮箱   生成验证链接


        # 查询类型存在
        etype = int(etype)
        with self.M('mail_type') as obj:
            etype_exit = obj.where('id =?', etype).count()
        if not etype_exit:
            # 无对应类型跳过
            return

        # 插入邮箱
        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            # 有退订 改为订阅
            exit_un = obj.where('recipient', email).where('etype', etype).where('active', 0).count()
            if exit_un:
                obj.where('recipient', email).where('etype', etype).update({'active': 1})
                return

            # 不存在 新增
            exit = obj.where('recipient', email).where('etype', etype).where('active', 1).count()
            if not exit:
                created = int(time.time())
                insert = {
                    'created': created,
                    'recipient': email,
                    'etype': etype,
                    'active': 1,
                }
                obj.insert(insert)
        return


    # 退订接口调用的提交黑名单
    def submit_recipient_blacklist(self, args):

        email = args.email
        etypes = args.etypes
        task_id = args.task_id
        subject = args.subject
        send_time = args.send_time

        created = int(time.time())
        etype_list = etypes.split(",")

        with self.M('mail_type') as obj:
            data_list = obj.select()
        types = {str(item["id"]): item["mail_type"] for item in data_list}
        try:
            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                for etype in etype_list:
                    etype = int(etype)

                    if not types.get(str(etype), None):
                        continue

                    # 有退订 跳过
                    exit_un = obj.where('recipient', email).where('etype', etype).where('active', 0).count()
                    if exit_un:
                        continue

                    # 有订阅 改为退订记录任务
                    exit = obj.where('recipient', email).where('etype', etype).where('active', 1).count()
                    if exit:
                        # 更新退订时间
                        bb = obj.where('recipient', email).where('etype', etype).update({'active': 0, 'task_id': task_id, 'created':created})

                        continue
            return True
        except Exception as e:
            # public.print_log(public.get_error_info())
            return False


    # 获取退订类型
    def get_mail_type_list(self, get):
        email = get.get('email', '')
        if not email:
            # return 'There is no email'
            return {"status": False, "msg": public.lang("There is no email")}

        with self.M('mail_type') as obj:
            typelist = obj.order('created desc').select()
        typelist = {str(item["id"]): item["mail_type"] for item in typelist}

        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            mail_type = []
            etypes = obj.where('active', 1).where('recipient like ?', '{}%'.format(email)).field('etype').select()


            for j in etypes:
                if typelist.get(str(j['etype']), None):
                    mail_type.append({'id': j['etype'], 'mail_type':typelist[str(str(j['etype']))]})


        # return mail_type
        return {"status":True, "msg": mail_type}

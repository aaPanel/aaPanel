#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
#-------------------------------------------------------------------

# 上传文件至oss
#------------------------------
import os
from filesModel.base import filesBase
import public,smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

class main(filesBase):


    def __init__(self):
        pass


    def get_oss_objects(self,get):
        """
        @name 获取可上传的对象存储
        """
        return  self.get_all_objects(get)



    def get_file_list(self,get):
        """
        @name 获取可上传的对象存储
        """
        return self.get_base_objects(get)



    def check_email_config(self,get):
        """
        @name 检测邮箱是否配置
        """
        import config

        c_obj = config.config()
        mail_config = c_obj.get_msg_configs(get)['mail']

        return mail_config

    def send_to_email(self,get):
        """
        @name 发送文件到邮件
        @flist list 文件列表
        @msg string  邮件正文
        @to string 邮件接收人，多个逗号隔开
        """

        import config
        c_obj = config.config()

        try:
            mail_config = c_obj.get_msg_configs(get)['mail']['data']
            if not mail_config :
                return public.returnMsg(False,'未正确配置邮箱信息。')

            if not mail_config['send']['qq_mail']:
                return public.returnMsg(False,'未正确配置邮箱信息。')
        except:
            return public.returnMsg(False,'未正确配置邮箱信息。')

        msg = get.msg
        receive_list = get.to_email.split(',')
        if len(receive_list) <= 0:
            return public.returnMsg(False,'发送失败，接收者不能为空.')


        #附件文件
        flist = []
        if 'flist' in get: flist = get.flist

        result = {}
        result['status'] = True
        result['list'] = {}
        for email in receive_list:
            slist = {}
            try:
                data = MIMEMultipart()
                data['From'] = formataddr([mail_config['send']['qq_mail'], mail_config['send']['qq_mail']])
                data['To'] = formataddr([mail_config['send']['qq_mail'], email.strip()])
                data['Subject'] = '宝塔面板消息通知'
                if int(mail_config['send']['port']) == 465:
                    server = smtplib.SMTP_SSL(str(mail_config['send']['hosts']), str(mail_config['send']['port']))
                else:
                    server = smtplib.SMTP(str(mail_config['send']['hosts']), str(mail_config['send']['port']))

                data.attach(MIMEText(msg, 'html', 'utf-8'))

                slist['error'] = {}
                #添加附件
                for filename in flist:
                    if not os.path.exists(filename):
                        slist['error'][filename] = '文件不存在'
                        continue

                    #超过50M无法发送
                    if os.path.getsize(filename) > 50 * 1024 *1024:
                        slist['error'][filename] = '文件大于50M'
                        continue

                    #中文无法发送
                    if public.check_chinese(filename):
                        slist['error'][filename] = '文件名包含中文，发送失败.'
                        continue

                    att1 = MIMEText(open(filename, 'rb').read(), 'base64', 'utf-8')
                    att1["Content-Type"] = 'application/octet-stream'
                    att1["Content-Disposition"] = 'attachment; filename="' + os.path.basename(filename) + '"'
                    data.attach(att1)

                server.login(mail_config['send']['qq_mail'], mail_config['send']['qq_stmp_pwd'])
                server.sendmail(mail_config['send']['qq_mail'], [email.strip(), ], data.as_string())
                server.quit()
                slist['status'] = True
            except :
                slist = '发送失败,' + public.get_error_info()

            result['list'][email] = slist
        public.set_module_logs('files_send_to_email', 'send_to_email', 1)
        return result



    def upload_file(self,args):
        """
        @name 上传文件到指定的对象存储
        """

        name = args.name
        filename = args.filename
        bucket = args.object_name.rstrip('/')

        if not os.path.exists(filename):
            return public.returnMsg(False,'FILE_NOT_EXIST')

        info = self.get_soft_find(name)
        if not info['setup']:
            return public.returnMsg(False,'未安装[{}]插件'.format(info['title']))

        sfile = '{path}/plugin/{name}/{name}_main.py'.format(path=public.get_panel_path(),name=name)
        if public.readFile(sfile).find('upload_to') == -1:
            return public.returnMsg(False,'暂不支持该操作，请将[{}]插件升级到最新版'.format(info['title']))

        #创建任务
        import panelTask
        task_obj = panelTask.bt_task()
        msg = '上传文件{}到{}'.format(filename,info['title'])
        exec_shell = 'btpython -u {spath} upload_to {file} {bucket}/{filename}'.format(spath=sfile,file=filename,bucket=bucket,filename=os.path.basename(filename))
        task_obj.create_task(msg, 0, exec_shell)

        public.set_module_logs('files_upload_to_file', 'upload_file', 1)
        public.WriteLog('TYPE_FILE', msg)
        return public.returnMsg(True, '已添加到上传队列.')





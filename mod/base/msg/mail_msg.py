#coding: utf-8
# +-------------------------------------------------------------------
# | aapanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aapanel(http://www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# | Author: lx
# | 消息通道邮箱模块
# +-------------------------------------------------------------------

import smtplib
import traceback
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Tuple, Union, Optional
import public

from mod.base.msg.util import write_push_log, write_mail_push_log, get_test_msg


class MailMsg:

    def __init__(self, mail_data):
        self.id = mail_data["id"]
        self.config = mail_data["data"]

    @classmethod
    def check_args(cls, args: dict) -> Tuple[bool, Union[dict, str]]:
        if "send" not in args or "receive" not in args or len(args["receive"]) < 1:
            return False, "Incomplete information, there must be a sender and at least one receiver"

        if "title" not in args:
            return False, "There is no necessary remark information"

        title = args["title"]
        if len(title) > 15:
            return False, 'Note names cannot be longer than 15 characters'

        send_data = args["send"]
        send = {}
        for i in ("qq_mail", "qq_stmp_pwd", "hosts", "port"):
            if i not in send_data:
                return False, "The sender configuration information is incomplete"
            send[i] = send_data[i].strip()

        receive_data = args["receive"]
        if isinstance(receive_data, str):
            receive_list = [i.strip() for i in receive_data.split("\n") if i.strip()]
        else:
            receive_list = [i.strip() for i in receive_data if i.strip()]

        data = {
            "send": send,
            "title": title,
            "receive": receive_list,
        }

        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>configuration state: Success<br>']
        }

        test_task = get_test_msg("Message channel configuration reminders")

        res = test_obj.send_msg(
            test_task.to_mail_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )
        if res is None or res.find("Failed to send mail to some recipients") != -1:
            return True, data

        return False, res

    def send_msg(self, msg: str, title: str):
        """
        邮箱发送
        @msg 消息正文
        @title 消息标题
        """
        if not self.config:
            return public.lang('Mailbox information is not configured correctly')

        if 'port' not in self.config['send']: 
            self.config['send']['port'] = 465

        receive_list = self.config['receive']

        error_list, success_list = [], []
        error_msg_dict = {}
        for email in receive_list:
            if not email.strip():
                continue
            try:
                data = MIMEText(msg, 'html', 'utf-8')
                data['From'] = formataddr((self.config['send']['qq_mail'], self.config['send']['qq_mail']))
                data['To'] = formataddr((self.config['send']['qq_mail'], email.strip()))
                data['Subject'] = title
                if int(self.config['send']['port']) == 465:
                    server = smtplib.SMTP_SSL(str(self.config['send']['hosts']), int(self.config['send']['port']))
                else:
                    server = smtplib.SMTP(str(self.config['send']['hosts']), int(self.config['send']['port']))

                server.login(self.config['send']['qq_mail'], self.config['send']['qq_stmp_pwd'])
                server.sendmail(self.config['send']['qq_mail'], [email.strip(), ], data.as_string())
                server.quit()
                success_list.append(email)
            except:
                error_list.append(email)
                error_msg_dict[email] = traceback.format_exc()

        if not error_list and not success_list:  # 没有接收者
            return public.lang('The receiving mailbox is not configured')
        if not error_list:
            write_push_log("mail", True, title, success_list)  # 没有失败
            return None
        if not success_list:
            write_push_log("mail", False, title, error_list)  # 全都失败
            return public.lang('Failed to send message, Recipient of failed to send:{}',error_list)
        write_mail_push_log(title, error_list, success_list)

        return public.lang('Failed to send mail to some recipients, including:{}',error_list)

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>configuration state: <font color=#20a53a> Success </font>\n\n']
        }
        test_task = get_test_msg("Message channel configuration reminders")
        res = self.send_msg(
            test_task.to_mail_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )
        if res is None:
            return None
        return res


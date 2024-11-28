import time
import traceback

from mod.base.push_mod import SenderConfig
from .weixin_msg import WeiXinMsg
from .mail_msg import MailMsg
from .tg_msg import TgMsg
from .web_hook_msg import WebHookMsg
from .feishu_msg import FeiShuMsg
from .dingding_msg import DingDingMsg
from .sms_msg import SMSMsg
# from .wx_account_msg import WeChatAccountMsg
import json
from mod.base import json_response
from .util import write_file, read_file
import sys,os
sys.path.insert(0, "/www/server/panel/class/")
import public

# 短信会自动添加到 sender 库中的第一个 且通过官方接口更新
# 微信公众号信息通过官网接口更新， 不写入数据库，需要时由文件中读取并序列化
# 其他告警通道本质都类似于web hook 在确认完数据信息无误后，都可以自行添加或启用
class SenderManager:
    def __init__(self):
        self.custom_parameter_filename = "/www/server/panel/data/mod_push_data/custom_parameter.pl"
        self.init_default_sender()
    def set_sender_conf(self, get):

        args = json.loads(get.sender_data.strip())

        try:
            sender_id = None
            try:
                if hasattr(get, "sender_id"):
                    sender_id = get.sender_id.strip()
                    if not sender_id:
                        sender_id = None
                sender_type = get.sender_type.strip()
                args = json.loads(get.sender_data.strip())
            except (json.JSONDecoder, AttributeError, TypeError):
                return json_response(status=False, msg=public.lang('The parameter is incorrect'))
            sender_config = SenderConfig()
            if sender_id is not None:
                tmp = sender_config.get_by_id(sender_id)
                if tmp is None:
                    sender_id = None

            if sender_type == "weixin":
                data = WeiXinMsg.check_args(args)
                if isinstance(data, str):
                    return json_response(status=False, data=data, msg=public.lang('Test send failed'))


            elif sender_type == "mail":
                _, data = MailMsg.check_args(args)
                if isinstance(data, str):
                    return json_response(status=False, data=data, msg=public.lang('Test send failed'))


            elif sender_type == "tg":
                _, data = TgMsg.check_args(args)

                if isinstance(data, str):
                    return json_response(status=False, data=data, msg=data)
            elif sender_type == "webhook":
                custom_parameter = args.get("custom_parameter", {})
                if custom_parameter:
                    try:
                        public.writeFile(self.custom_parameter_filename, json.dumps(custom_parameter))
                    except:
                        pass


                data = WebHookMsg.check_args(args)
                if isinstance(data, str):
                    return json_response(status=False, data=data, msg=public.lang('Test send failed'))

                # 从文件读取并删除文件
                try:
                    if os.path.exists(self.custom_parameter_filename):
                        custom_parameter = json.loads(public.readFile(self.custom_parameter_filename))
                        data['custom_parameter'] = custom_parameter
                        os.remove(self.custom_parameter_filename)
                except:
                    pass

            elif sender_type == "feishu":
                data = FeiShuMsg.check_args(args)
                if isinstance(data, str):
                    return json_response(status=False, data=data, msg=public.lang('Test send failed'))

            elif sender_type == "dingding":
                data = DingDingMsg.check_args(args)
                if isinstance(data, str):
                    return json_response(status=False, data=data, msg=public.lang('Test send failed'))
            else:
                return json_response(status=False, msg=public.lang('A type that is not supported by the current interface'))
                # Check if the sender configuration already exists

            existing_sender = any(
                conf for conf in sender_config.config
                if conf['sender_type'] == sender_type and 'title' in conf['data'] and conf['data']['title'] == data['title'] and conf['id'] != sender_id
            )


            # for conf in sender_config.config:
            #     if conf['sender_type'] == sender_type and 'title' in conf['data'] and conf['data']['title'] == data[
            #         'title'] and conf['id'] != sender_id:
            #         public.print_log('000   -{}'.format(conf['sender_type']))
            #         public.print_log('000   -{}'.format(sender_type))
            #
            #         public.print_log('111 conf  -{}'.format(conf['sender_type']))
            #         public.print_log('111   -{}'.format(sender_type))
            #
            #         public.print_log('222 conf -{}'.format(conf['data']['title']))
            #         public.print_log('222 data  -{}'.format(data['title']))
            #
            #         public.print_log('333 conf  -{}'.format(conf['id']))
            #         public.print_log('333   -{}'.format(sender_id))

            if existing_sender:
                return json_response(status=False, msg=public.lang('The same send configuration already exists and cannot be added repeatedly'))
            now_sender_id = None
            if not sender_id:
                now_sender_id = sender_config.nwe_id()
                sender_config.config.append(
                    {
                        "id": now_sender_id,
                        "sender_type": sender_type,
                        "data": data,
                        "used": True,
                    })

            else:
                now_sender_id = sender_id
                tmp = sender_config.get_by_id(sender_id)
                tmp["data"].update(data)

            # type_senders = [conf for conf in sender_config.config if conf['sender_type'] == sender_type]
            # if len(type_senders) == 1:
            #     for conf in sender_config.config:
            #         conf["original"] = (conf['id'] == now_sender_id)

            sender_config.save_config()
            if sender_type == "webhook":
                self.set_default_for_compatible(sender_config.get_by_id(now_sender_id))

            return json_response(status=True, msg=public.lang('Saved successfully'))
        except:
            public.print_log('Error:{}'.format(str(public.get_error_info())))

    @staticmethod
    def change_sendr_used(get):
        try:
            sender_id = get.sender_id.strip()
        except (AttributeError, TypeError):
            return json_response(status=False, msg=public.lang('The parameter is incorrect'))

        sender_config = SenderConfig()
        tmp = sender_config.get_by_id(sender_id)
        if tmp is None:
            return json_response(status=False, msg=public.lang('Corresponding sender not found'))
        tmp["used"] = not tmp["used"]

        sender_config.save_config()

        return json_response(status=True, msg=public.lang('Saved successfully'))

    @staticmethod
    def remove_sender(get):
        try:
            sender_id = get.sender_id.strip()
        except (AttributeError, TypeError):
            return json_response(status=False, msg=public.lang('The parameter is incorrect'))

        sender_config = SenderConfig()
        tmp = sender_config.get_by_id(sender_id)
        if tmp is None:
            return json_response(status=False, msg=public.lang('Corresponding sender not found'))
        sender_config.config.remove(tmp)
        sender_config.save_config()

        return json_response(status=True, msg=public.lang('Successfully delete'))

    @staticmethod
    def get_sender_list(get):
        # 微信， 飞书， 钉钉， web-hook， 邮箱
        refresh = False
        try:
            if hasattr(get, 'refresh'):
                refresh = get.refresh.strip()
                if refresh in ("1", "true"):
                    refresh = True
        except (AttributeError, TypeError):
            return json_response(status=False, msg=public.lang('The parameter is incorrect'))

        res = []
        # WeChatAccountMsg.refresh_config(force=refresh)
        simple = ("weixin", "mail", "webhook", "feishu", "dingding", "tg")

        for conf in SenderConfig().config:
            if conf["sender_type"] in simple or conf["sender_type"] == "wx_account":
                res.append(conf)
            # 去掉短信设置
            # elif conf["sender_type"] == "sms":
            #     conf["data"] = SMSMsg(conf).refresh_config(force=refresh)
            #     res.append(conf)
        res.sort(key=lambda x: x["sender_type"])
        return json_response(status=True, data=res)

    @staticmethod
    def test_send_msg(get):
        try:
            sender_id = get.sender_id.strip()
        except (json.JSONDecoder, AttributeError, TypeError):
            return json_response(status=False, msg=public.lang('The parameter is incorrect'))

        sender_config = SenderConfig()
        tmp = sender_config.get_by_id(sender_id)
        if tmp is None:
            return json_response(status=False, msg=public.lang('Corresponding sender not found'))

        sender_type = tmp["sender_type"]

        if sender_type == "weixin":
            sender_obj = WeiXinMsg(tmp)

        elif sender_type == "mail":
            sender_obj = MailMsg(tmp)

        elif sender_type == "webhook":
            sender_obj = WebHookMsg(tmp)

        elif sender_type == "feishu":
            sender_obj = FeiShuMsg(tmp)

        elif sender_type == "dingding":
            sender_obj = DingDingMsg(tmp)
        elif sender_type == "tg":
            sender_obj = TgMsg(tmp)
        # elif sender_type == "wx_account":
        #     sender_obj = WeChatAccountMsg(tmp)
        else:
            return json_response(status=False, msg=public.lang('A type that is not supported by the current interface'))

        res = sender_obj.test_send_msg()
        if isinstance(res, str):
            return json_response(status=False, data=res, msg=public.lang('Test send failed'))
        return json_response(status=True, msg=public.lang('The sending was successful'))

    @staticmethod
    def set_default_for_compatible(sender_data: dict):
        if sender_data["sender_type"] in ("sms", "wx_account"):
            return

        panel_data = "/www/server/panel/data"
        if sender_data["sender_type"] == "weixin":
            weixin_file = "{}/weixin.json".format(panel_data)
            write_file(weixin_file, json.dumps({
                "state": 1,
                "weixin_url": sender_data["data"]["url"],
                "title": sender_data["data"]["title"],
                "list": {
                    "default": {
                        "data": sender_data["data"]["url"],
                        "title": sender_data["data"]["title"],
                        "status": 1,
                        "addtime": int(time.time())
                    }
                }
            }))

        elif sender_data["sender_type"] == "mail":
            stmp_mail_file = "{}/stmp_mail.json".format(panel_data)
            mail_list_file = "{}/mail_list.json".format(panel_data)
            write_file(stmp_mail_file, json.dumps(sender_data["data"]["send"]))
            write_file(mail_list_file, json.dumps(sender_data["data"]["receive"]))

        elif sender_data["sender_type"] == "feishu":
            feishu_file = "{}/feishu.json".format(panel_data)
            write_file(feishu_file, json.dumps({
                "feishu_url": sender_data["data"]["url"],
                "title": sender_data["data"]["title"],
                "isAtAll": True,
                "user": []
            }))

        elif sender_data["sender_type"] == "dingding":
            dingding_file = "{}/dingding.json".format(panel_data)
            write_file(dingding_file, json.dumps({
                "dingding_url": sender_data["data"]["url"],
                "title": sender_data["data"]["title"],
                "isAtAll": True,
                "user": []
            }))
        elif sender_data["sender_type"] == "tg":
            tg_file = "{}/tg_bot.json".format(panel_data)
            write_file(tg_file, json.dumps({
                "my_id": sender_data["data"]["my_id"],
                "bot_token": sender_data["data"]["bot_token"],
                "title": sender_data["data"]["title"]
            }))
        elif sender_data["sender_type"] == "webhook":
            webhook_file = "{}/hooks_msg.json".format(panel_data)
            try:
                webhook_data = json.loads(read_file(webhook_file))
            except:
                webhook_data =[]
            target_idx = -1
            for idx, i in enumerate(webhook_data):
                if i["name"] == sender_data["data"]["title"]:
                    target_idx = idx
                    break
            else:
                sender_data["data"]["name"] = sender_data["data"]["title"]
                webhook_data.append(sender_data["data"])
            if target_idx != -1:
                sender_data["data"]["name"] = sender_data["data"]["title"]
                webhook_data[target_idx] = sender_data["data"]
            write_file(webhook_file, json.dumps(webhook_data))


    def init_default_sender(self):


        import os,sys
        sys.path.insert(0, "/www/server/panel/mod/project/push")
        import msgconfMod
        sender_config = SenderConfig()
        sender_types = set(conf['sender_type'] for conf in sender_config.config)
        all_types = {"feishu", "dingding", "weixin", "mail", "webhook"}  # 所有可能的类型

        for sender_type in sender_types:
            type_senders = [conf for conf in sender_config.config if conf['sender_type'] == sender_type]

            # 检查是否已有默认通道
            has_default = any(conf.get('original', False) for conf in type_senders)
            if has_default:
                continue

            if len(type_senders) == 1:
                # 只有一个通道，设置为默认通道
                for conf in type_senders:
                    get = public.dict_obj()
                    get['sender_id'] = conf['id']
                    get['sender_type'] = conf['sender_type']
                    self.set_default_sender(get)
            else:
                # 有多个通道，根据添加时间设置默认通道
                sorted_senders = sorted(type_senders, key=lambda x: x['data'].get('create_time', ''))
                if sorted_senders:
                    get = public.dict_obj()
                    get['sender_id'] = sorted_senders[0]['id']
                    get['sender_type'] = sorted_senders[0]['sender_type']
                    self.set_default_sender(get)

        # 检查没有通道的类型，并删除对应文件
        missing_types = all_types - sender_types
        for missing_type in missing_types:
            file_path = f"/www/server/panel/data/{missing_type}.json"
            if os.path.exists(file_path):
                os.remove(file_path)
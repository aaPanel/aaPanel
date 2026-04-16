from typing import Union, Optional, Tuple
from .send_tool import WxAccountMsg


# 告警系统在处理每个任务时，都会重新建立有一个Task的对象，(请勿在__init__的初始化函数中添加任何参数)
# 故每个对象中都可以大胆存放本任务所有数据，不会影响同类型的其他任务
class BaseTask:

    def __init__(self):
        self.source_name: str = ''
        self.title: str = ''  # 这个是告警任务的标题(根据实际情况改变)
        self.template_name: str = ''  # 这个告警模板的标题(不会改变)

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查设置的告警参数（是否合理）
        @param task_data: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        raise NotImplementedError()

    def get_keyword(self, task_data: dict) -> str:
        """
        返回一个关键字，用于后续查询或执行任务时使用， 例如：防篡改告警，可以根据其规则id生成一个关键字，
        后续通过规则id和来源tamper 查询并使用
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        raise NotImplementedError()

    def get_title(self, task_data: dict) -> str:
        """
        返回一个标题
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        if self.title:
            return self.title
        return self.template_name

    def task_run_end_hook(self, res: dict) -> None:
        """
        在告警系统中。执行完了任务后，会去掉用这个函数
        @type res: dict, 执行任务的结果
        @return:
        """
        return

    def task_config_update_hook(self, task: dict) -> None:
        """
        在告警管理中。更新任务数据后，会去掉用这个函数
        @return:
        """
        return

    def task_config_remove_hook(self, task: dict) -> None:
        """
        在告警管理中。移除这个任务后，会去掉用这个函数
        @return:
        """
        return

    def task_config_create_hook(self, task: dict) -> None:
        """
        在告警管理中。新建这个任务后，会去掉用这个函数
        @return:
        """
        return

    def check_time_rule(self, time_rule: dict) -> Union[dict, str]:
        """
        检查和修改设置的告警的时间控制参数是是否合理
        可以添加参数 get_by_func 字段用于指定使用本类中的那个函数执行时间判断标准, 替换标准的时间规则判断功能
         ↑示例如本类中的: can_send_by_time_rule
        @param time_rule: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        return time_rule

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        """
        检查和修改设置的告警的次数控制参数是是否合理
        可以添加参数 get_by_func 字段用于指定使用本类中的那个函数执行次数判断标准, 替换标准的次数规则判断功能
         ↑示例如本类中的: can_send_by_num_rule
        @param num_rule: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        return num_rule

    def can_send_by_num_rule(self, task_id: str, task_data: dict, number_rule: dict, push_data: dict) -> Optional[str]:
        """
        这是一个通过函数判断是否能够发送告警的示例，并非每一个告警任务都需要有
        @param task_id: 任务id
        @param task_data: 告警参数信息
        @param number_rule: 次数控制信息
        @param push_data: 本次要发送的告警信息的原文，应当为字典, 来自 get_push_data 函数的返回值
        @return: 返回None
        """
        return None

    def can_send_by_time_rule(self, task_id: str, task_data: dict, time_rule: dict, push_data: dict) -> Optional[str]:
        """
        这是一个通过函数判断是否能够发送告警的示例，并非每一个告警任务都需要有
        @param task_id: 任务id
        @param task_data: 告警参数信息
        @param time_rule: 时间控制信息
        @param push_data: 本次要发送的告警信息的原文，应当为字典, 来自 get_push_data 函数的返回值
        @return:
        """
        return None

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """
        判断这个任务是否需要返送
        @param task_id: 任务id
        @param task_data: 任务的告警参数
        @return: 如果触发了告警，返回一个dict的原文，作为告警信息，否则应当返回None表示未触发
                返回之中应当包含一个 msg_list 的键（值为List[str]类型），将主要的信息返回
                用于以下信息的自动序列化包含[dingding, feishu, mail, weixin, web_hook]
                短信和微信公众号由于长度问题，必须每个任务手动实现
        """
        raise NotImplementedError()

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        raise NotImplementedError()

    # push_public_data 公共的告警参数提取位置
    # 内容包含：
    #   ip  网络ip
    #   local_ip  本机ip
    #   time  时间日志的字符串
    #   timestamp  当前的时间戳
    #   server_name  服务器别名

    # --- 所有 to_xxx_msg 于 system.py中用于各种场景告警发送 send_message 调用, 用于定制化格式
    def to_dingding_msg(self, push_data: dict, push_public_data: dict) -> str:
        """钉钉消息"""
        msg_list = push_data.get('msg_list', None)
        if msg_list is None or not isinstance(msg_list, list):
            raise ValueError("Task: {} alert push data parameter error, there is no msg_list field".format(self.title))

        headers = self._format_public_headers(push_public_data)
        beautified_list = self._beautify_msg_list(msg_list)
        content = "\n\n".join(beautified_list)

        # 钉钉：确保标题包含 aapanel
        title = self.title
        if "aapanel" not in title.lower():
            title += " - aaPanel"

        return f"#### 🔔 {title}\n\n{headers}\n\n{content}"

    def to_feishu_msg(self, push_data: dict, push_public_data: dict) -> str:
        """飞书消息"""
        msg_list = push_data.get('msg_list', None)
        if msg_list is None or not isinstance(msg_list, list):
            raise ValueError("Task: {} alert push data parameter error, there is no msg_list field".format(self.title))

        headers = self._format_public_headers(push_public_data)
        beautified_list = self._beautify_msg_list(msg_list)
        content = "\n\n".join(beautified_list)

        return f"{headers}\n\n{content}"

    def to_mail_msg(self, push_data: dict, push_public_data: dict) -> str:
        """邮件消息"""
        msg_list = push_data.get('msg_list', None)
        if msg_list is None or not isinstance(msg_list, list):
            raise ValueError("Task: {} alert push data parameter error, there is no msg_list field".format(self.title))

        # 邮件使用 HTML 格式
        headers = self._format_public_headers(push_public_data)
        headers = headers.replace("####", "<h4>").replace("\n", "<br>")
        headers = headers.replace("🖥️", "&#128190;").replace("🌐", "&#127756;").replace("⏰", "&#9200;").replace("🔔",
                                                                                                               "&#128276;")

        beautified_list = self._beautify_msg_list(msg_list)
        # 保留图标或转换为 HTML 实体
        content_lines = []
        for msg in beautified_list:
            # 保留基本的 HTML 标签和图标
            msg = msg.replace("✅", "&#10004;").replace("❌", "&#10060;").replace("⚠️", "&#9888;").replace("⚙️",
                                                                                                         "&#9881;")
            content_lines.append(msg)

        content = "<br>".join(content_lines)

        return f"{headers}<br><br>{content}"

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        """
        返回 短信告警的类型和数据
        @param push_data:
        @param push_public_data:
        @return: 第一项是类型， 第二项是数据
        """
        raise NotImplementedError()

    def to_tg_msg(self, push_data: dict, push_public_data: dict) -> str:
        """Telegram 消息"""
        msg_list = push_data.get('msg_list', None)
        if msg_list is None or not isinstance(msg_list, list):
            raise ValueError("Task: {} alert push data parameter error, there is no msg_list field".format(self.title))

        headers = self._format_public_headers(push_public_data)
        beautified_list = self._beautify_msg_list(msg_list)
        content = "\n".join(beautified_list)

        # Telegram：转义特殊字符
        headers = self._escape_markdown(headers)
        content = self._escape_markdown(content)

        return f"{headers}\n{content}"

    def to_weixin_msg(self, push_data: dict, push_public_data: dict) -> str:
        """企业微信消息"""
        msg_list = push_data.get('msg_list', None)
        if msg_list is None or not isinstance(msg_list, list):
            raise ValueError("Task: {} alert push data parameter error, there is no msg_list field".format(self.title))

        headers = self._format_public_headers(push_public_data)
        beautified_list = self._beautify_msg_list(msg_list)

        # 企业微信：移除 HTML 标签，使用缩进
        headers = self._remove_html_tags(headers)
        content = "\n\n".join([self._remove_html_tags(m) for m in beautified_list])

        spc = "\n                "
        return f"{headers}{spc}{spc}{content.replace(chr(10), spc)}"

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        raise NotImplementedError()

    def to_web_hook_msg(self, push_data: dict, push_public_data: dict) -> str:
        """Webhook 消息"""
        msg_list = push_data.get('msg_list', None)
        if msg_list is None or not isinstance(msg_list, list):
            raise ValueError("Task: {} alert push data parameter error, there is no msg_list field".format(self.title))

        headers = self._format_public_headers(push_public_data)
        beautified_list = self._beautify_msg_list(msg_list)
        content = "\n".join(beautified_list)

        return f"{headers}\n{content}"

    def to_discord_msg(self, push_data: dict, push_public_data: dict) -> str:
        """Discord 消息"""
        msg_list = push_data.get('msg_list', None)
        if msg_list is None or not isinstance(msg_list, list):
            raise ValueError("Task: {} alert push data parameter error, there is no msg_list field".format(self.title))

        headers = self._format_public_headers(push_public_data)
        beautified_list = self._beautify_msg_list(msg_list)
        content = "\n".join(beautified_list)

        # 清理HTML标签
        import re
        headers = re.sub(r'<[^>]+>', '', headers)
        content = re.sub(r'<[^>]+>', '', content)

        return f"{headers}\n{content}"

    # ==================== 消息格式化辅助方法 ====================

    def _format_public_headers(self, push_public_data: dict) -> str:
        """
        格式化公共头部
        @param push_public_data: 公共数据
        @return: 格式化后的头部字符串
        """
        return (
            f"#### 🔔 {self.title}\n"
            f"> 🖥️ Server: {push_public_data['server_name']}\n"
            f"> 🌐 IP: {push_public_data['ip']}(Public) {push_public_data['local_ip']}(Private)\n"
            f"> ⏰ Time: {push_public_data['time']}"
        )

    def _beautify_msg_list(self, msg_list: list) -> list:
        """
        美化消息列表
        - 添加状态图标
        - 优化格式
        @param msg_list: 原始消息列表
        @return: 美化后的消息列表
        """
        if not msg_list:
            return []

        icons = {
            "success": "✅",
            "fail": "❌",
            "error": "❌",
            "warning": "⚠️",
            "config": "⚙️",
            "completed": "⚙️",
        }

        beautified = []
        for msg in msg_list:
            icon = ""
            msg_lower = msg.lower()
            for keyword, icon_char in icons.items():
                if keyword in msg_lower:
                    icon = icon_char
                    break
            # 如果消息以 > 开头，图标放在 > 之后
            if msg.startswith(">"):
                msg = f"> {icon} {msg[1:].lstrip()}" if icon else msg
            else:
                msg = f"{icon} {msg}" if icon else msg

            beautified.append(msg)
        return beautified

    def _remove_html_tags(self, text: str) -> str:
        """
        移除 HTML 标签（保留内容）
        主要用于企业微信通道
        @param text: 原始文本
        @return: 移除标签后的文本
        """
        import re
        return re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)

    def _escape_markdown(self, text: str) -> str:
        """
        转义 Telegram Markdown 特殊字符
        只转义需要转义的字符，保留 Markdown 语法字符（如 # >）
        @param text: 原始文本
        @return: 转义后的文本
        """
        # Telegram Markdown 需要转义的字符（不包含 # > .，要保留标题、引用和IP格式）
        escape_chars = r'*_[]()~`+-=|{}!'

        for ch in escape_chars:
            text = text.replace(ch, '\\' + ch)

        return text

    # ==================== 原 public_headers_msg 方法, 可以继续使用 ====================

    def public_headers_msg(self, push_public_data: dict, spc: str = None, dingding=False) -> str:
        """
        原方法
        @deprecated: 建议使用 _format_public_headers()
        """
        if spc is None:
            spc = "\n\n"
        title = self.title
        if dingding and "aapanel" not in title:
            title += "aapanel"
        return spc.join([
            "#### {}".format(title),
            ">Server:" + push_public_data['server_name'],
            ">IPAddress: {}(Internet) {}(Internal)".format(push_public_data['ip'], push_public_data['local_ip']),
            ">SendingTime: " + push_public_data['time']
        ])


class BaseTaskViewMsg:

    def get_msg(self, task: dict) -> Optional[str]:
        return ""

# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: jose <zhw@aapanel.com>
# | 消息通道电报模块 (Refactored for unified Markdown formatting)
# +-------------------------------------------------------------------

import sys, os, re, public, json, requests

try:
    import telegram
except:
    public.ExecShell("btpip install -I python-telegram-bot")
    import telegram

panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0, panelPath + "/class/")
from requests.packages import urllib3

# 关闭警告
urllib3.disable_warnings()

from typing import Union, Optional

from mod.base.msg.util import write_push_log, get_test_msg


class TgMsg:
    conf_path = "{}/data/tg_bot.json".format(panelPath)
    __tg_info = None
    __module_name = None
    __default_pl = "{}/data/default_msg_channel.pl".format(panelPath)

    def __init__(self, conf):
        self.conf = conf
        self.bot_token = self.conf['data']['bot_token']
        self.my_id = self.conf['data']['my_id']

    def get_version_info(self, get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = 'Use telegram bots to send receive panel notifications'
        data['version'] = '1.1'
        data['date'] = '2025-11-18'
        data['author'] = 'aaPanel'
        data['title'] = 'Telegram'
        data['help'] = 'http://www.aapanel.com'
        return data

    def get_config(self, get):
        """
        获取tg配置
        """
        data = {}
        if self.__tg_info:
            data = self.__tg_info
            data['default'] = self.__get_default_channel()
        return data

    def set_config(self, get):
        """
        设置tg bot
        @my_id tg id
        @bot_token 机器人token
        """
        if not hasattr(get, 'my_id') or not hasattr(get, 'bot_token'):
            return public.returnMsg(False, public.lang("Please fill in the complete information"))

        title = 'Default'
        if hasattr(get, 'title'):
            title = get.title
            if len(title) > 7:
                return public.returnMsg(False, public.lang("Note name cannot exceed 7 characters"))

        self.__tg_info = {"my_id": get.my_id.strip(), "bot_token": get.bot_token, "title": title}

        try:
            # Use unified Markdown formatting
            info = self._build_status_message(
                title="Configuration Status",
                status="✓ Success",
                is_test=True
            )
            ret = self.send_msg(info, get.my_id.strip(), get.bot_token)
        except:
            ret = self.send_msg(
                self._build_status_message(
                    title="aaPanel Alarm Test",
                    status="Test Message",
                    is_test=True
                ),
                get.my_id.strip(),
                get.bot_token
            )

        if ret:
            if 'default' in get and get['default']:
                public.writeFile(self.__default_pl, self.__module_name)

            public.writeFile(self.conf_path, json.dumps(self.__tg_info))
            return public.returnMsg(True, public.lang("successfully set"))
        else:
            return ret

    def _escape_markdown_v2(self, text: str) -> str:
        """
        Escape special characters for Telegram's MarkdownV2 mode.
        Only escapes content, not Markdown formatting characters.
        
        MarkdownV2 special chars that need escaping in content: _ * [ ] ( ) ~ ` > # + - = | { } . !
        """
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        for ch in escape_chars:
            text = text.replace(ch, '\\' + ch)
        return text

    def _build_status_message(self, title: str, status: str, details: dict = None, is_test: bool = False) -> str:
        """
        Build a unified Markdown formatted message for Telegram.
        Properly escapes content while preserving Markdown formatting.
        
        Args:
            title: Message title/header
            status: Status text (e.g., "✓ Success" or "✗ Failed")
            details: Optional dictionary with key-value details to display
            is_test: Whether this is a test message
        
        Returns:
            Formatted Markdown message (MarkdownV2 compatible)
        """
        lines = []
        
        # Title (bold)
        escaped_title = self._escape_markdown_v2(title)
        lines.append(f"*{escaped_title}*")
        lines.append("")

        # Details section
        if details:
            for key, value in details.items():
                escaped_key = self._escape_markdown_v2(key)
                escaped_value = self._escape_markdown_v2(str(value))
                lines.append(f"• *{escaped_key}:* {escaped_value}")
            lines.append("")

        # Status (bold)
        escaped_status = self._escape_markdown_v2(status)
        lines.append(f"*Status:* {escaped_status}")

        # Test indicator (italic)
        if is_test:
            lines.append("_This is a test message_")

        message = "\n".join(lines)
        return message

    def _convert_legacy_format_to_markdown(self, msg: str) -> str:
        """
        Convert legacy HTML/mixed format messages to standard Markdown.
        Handles old format: #### Title, >blockquote, <br>, <font> tags
        
        Example input:
            #### Message channel configuration reminders
            >Server:aaPanel Linux panel
            >IPAddress: 82.165.195.157
            >configuration state:  Success
        
        Example output:
            *Message channel configuration reminders*
            
            • *Server:* aaPanel Linux panel
            • *IPAddress:* 82.165.195.157
            • *configuration state:* Success
        """
        # Extract title from #### syntax
        title_match = re.search(r'#{4,}\s*(.+)', msg)
        title = title_match.group(1).strip() if title_match else "Notification"

        # Remove the title from message
        msg = re.sub(r'#{4,}\s*.+\n', '', msg)

        # Convert HTML line breaks to newlines
        msg = msg.replace('<br>', '\n')

        # Remove all HTML tags and convert color coding
        msg = re.sub(r'<font\s+color=#[0-9a-fA-F]+>', '', msg)
        msg = msg.replace('</font>', '')

        # Clean up blockquote markers and convert to Markdown bold for labels
        lines = []
        for line in msg.split('\n'):
            line = line.strip()
            if line.startswith('>'):
                # Remove > and parse as key:value or content
                line = line[1:].strip()
                
                # Check if it's a key:value pair
                if ':' in line:
                    parts = line.split(':', 1)
                    key = parts[0].strip()
                    value = parts[1].strip()
                    # Escape both key and value
                    escaped_key = self._escape_markdown_v2(key)
                    escaped_value = self._escape_markdown_v2(value)
                    # Format with Markdown bold for key
                    line = f"• *{escaped_key}:* {escaped_value}"
                else:
                    escaped_line = self._escape_markdown_v2(line)
                    line = f"• {escaped_line}"

            elif line:
                line = self._escape_markdown_v2(line)

            if line:
                lines.append(line)

        # Build formatted message
        escaped_title = self._escape_markdown_v2(title)
        formatted = f"*{escaped_title}*\n\n"
        formatted += "\n".join(lines)

        return formatted

    async def send_msg_async(self, bot_token: str, chat_id: str, msg: str) -> None:
        """
        Send message via Telegram asynchronously.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Recipient chat ID
            msg: Message content (already formatted and escaped for MarkdownV2)
        """
        bot = telegram.Bot(token=bot_token)
        await bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode='MarkdownV2'
        )

    def send_msg(self, msg: str, chat_id: str = None, bot_token: str = None) -> Optional[str]:
        """
        Send message to Telegram using unified Markdown formatting.
        
        Args:
            msg: Message content (can be legacy format or already formatted)
            chat_id: Recipient chat ID (defaults to self.my_id)
            bot_token: Bot token (defaults to self.bot_token)
        
        Returns:
            None on success, error message on failure
        """
        bot_token = bot_token or self.bot_token
        chat_id = chat_id or self.my_id
        msg = msg.strip()

        # Convert legacy format to Markdown if needed
        if msg.find("####") >= 0 or msg.find("<font") >= 0 or msg.find("<br>") >= 0:
            msg = self._convert_legacy_format_to_markdown(msg)
        # If message is already formatted, don't escape again

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.send_msg_async(bot_token, chat_id, msg))
            write_push_log("Telegram", True, "Message sent")
            public.print_log('Message sent successfully!')
            loop.close()
            return None
        except Exception as e:
            error_msg = str(public.get_error_info())
            public.print_log(f'Telegram send error: {error_msg}')
            write_push_log("Telegram", False, "Send failed")
            return public.lang("Telegram failed to send: {}", error_msg)

    @classmethod
    def check_args(cls, args: dict) -> Union[tuple, str]:
        """
        Validate and test Telegram configuration arguments.
        """
        my_id = args.get('my_id', None)
        bot_token = args.get('bot_token', None)

        if not my_id or not bot_token:
            return False, public.lang('Incomplete information')

        my_id = my_id.strip()
        title = args.get('title', 'Default')

        if len(title) > 15:
            return False, public.lang('Note name cannot exceed 15 characters')

        data = {
            "my_id": my_id,
            "bot_token": bot_token,
            "title": title
        }
        conf = {"data": data}

        # Test the configuration
        tg = TgMsg(conf)
        try:
            test_msg = tg._build_status_message(
                title="aaPanel Configuration Test",
                status="✓ Configuration Successful",
                details={
                    "Panel": "aaPanel",
                    "Message Channel": "Telegram"
                },
                is_test=True
            )
            ret = tg.send_msg(test_msg)
        except Exception as e:
            test_msg = tg._build_status_message(
                title="aaPanel Alarm Test",
                status="✓ Test Message Sent",
                is_test=True
            )
            ret = tg.send_msg(test_msg)

        if ret:
            return False, ret
        else:
            return True, data

    def test_send_msg(self) -> Optional[str]:
        """
        Send a test message using the current configuration.
        """
        test_msg = self._build_status_message(
            title="aaPanel Configuration Test",
            status="✓ Configuration Successful",
            details={
                "Panel": "aaPanel",
                "Message Channel": "Telegram"
            },
            is_test=True
        )
        res = self.send_msg(test_msg)
        return res

    def push_data(self, data: dict) -> Optional[str]:
        """
        Unified interface to send notification data via Telegram.
        
        Args:
            data: Dictionary containing notification data
                  {"module":"mail", "title":"title", "msg":"content", ...}
        
        Returns:
            None on success, error message on failure
        """
        msg = data.get('msg', '')
        return self.send_msg(msg)

    def __get_default_channel(self) -> bool:
        """
        Check if Telegram is the default notification channel.
        """
        try:
            if public.readFile(self.__default_pl) == self.__module_name:
                return True
        except:
            pass
        return False

    def uninstall(self) -> None:
        """
        Remove Telegram configuration on uninstall.
        """
        if os.path.exists(self.conf_path):
            os.remove(self.conf_path)

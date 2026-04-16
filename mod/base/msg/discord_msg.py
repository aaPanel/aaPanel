# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# | Discord notification channel module
# +-------------------------------------------------------------------

import json
import requests
from typing import Optional, Union

from .util import write_push_log, get_test_msg
import public

# Disable SSL warnings
try:
    from requests.packages import urllib3
    urllib3.disable_warnings()
except:
    pass


class DiscordMsg:
    """Discord message channel"""

    def __init__(self, discord_data: dict):
        self.id = discord_data["id"]
        self.config = discord_data["data"]

    @classmethod
    def check_args(cls, args: dict) -> Union[dict, str]:
        """
        Validate Discord configuration parameters
        @param args: Configuration arguments
        @return: Validated data dict on success, error message string on failure
        """
        if "url" not in args or "title" not in args:
            return public.lang('Incomplete information')

        title = args["title"]
        if len(title) > 15:
            return public.lang('Note names cannot be longer than 15 characters')

        url = args["url"].strip()
        if not url:
            return public.lang('Webhook URL cannot be empty')

        # Validate URL format
        if not url.startswith("https://discord.com/api/webhooks/"):
            return public.lang('Invalid Discord Webhook URL format')

        data = {
            "url": url,
            "title": title
        }

        # Test send
        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>configuration state: Success']
        }
        test_task = get_test_msg("Message channel configuration reminders")

        res = test_obj.send_msg(
            test_task.to_discord_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )

        if res is None:
            return data

        return res

    def send_msg(self, msg: str, title: str) -> Optional[str]:
        """
        Send Discord message
        @param msg: Message content (Markdown format)
        @param title: Message title
        @return: None on success, error message string on failure
        """
        if not self.config:
            return public.lang('Discord information is not configured correctly')

        url = self.config.get("url", "")
        if not url:
            return public.lang('Discord Webhook URL is not configured')

        try:
            # Simple text message format
            payload = {
                "content": msg
            }

            headers = {'Content-Type': 'application/json'}

            response = requests.post(
                url=url,
                data=json.dumps(payload),
                headers=headers,
                timeout=10,
                verify=False
            )

            if response.status_code in [200, 204]:
                write_push_log("Discord", True, title)
                return None
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                write_push_log("Discord", False, title)
                return error_msg

        except Exception as e:
            error_msg = f"Discord send failed: {str(e)}"
            write_push_log("Discord", False, title)
            return error_msg

    def test_send_msg(self) -> Optional[str]:
        """
        Test send message
        @return: None on success, error message string on failure
        """
        test_msg = {
            "msg_list": ['>configuration state: <font color=#20a53a>Success</font>']
        }
        test_task = get_test_msg("Message channel configuration reminders")

        res = self.send_msg(
            test_task.to_discord_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )

        if res is None:
            return None
        return res
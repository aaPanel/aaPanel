# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aapanel(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 新告警的所有数据库操作
# ------------------------------
import json
import os
from typing import Any, Dict, Optional, List
from uuid import uuid4

from .util import read_file, write_file


PANEL_PATH = "/www/server/panel"
PUSH_DATA_PATH = "{}/data/mod_push_data".format(PANEL_PATH)
UPDATE_VERSION_FILE = "{}/update_panel.pl".format(PUSH_DATA_PATH)
UPDATE_MOD_PUSH_FILE = "{}/update_mod.pl".format(PUSH_DATA_PATH)


class BaseConfig:
    """配置基类 - JSON 文件读写"""
    config_file_path = ""

    def __init__(self):
        if not os.path.exists(PUSH_DATA_PATH):
            os.makedirs(PUSH_DATA_PATH)
        self._config: Optional[List[Dict[str, Any]]] = None

    @property
    def config(self) -> List[Dict[str, Any]]:
        """懒加载获取配置列表"""
        if self._config is None:
            try:
                self._config = json.loads(read_file(self.config_file_path))
            except:
                self._config = []
        return self._config

    def save_config(self) -> None:
        """保存配置到文件"""
        write_file(self.config_file_path, json.dumps(self.config))

    @staticmethod
    def nwe_id() -> str:
        """生成唯一 ID"""
        return uuid4().hex[::2]

    def get_by_id(self, target_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 查找配置项"""
        for i in self.config:
            if i.get("id", None) == target_id:
                return i


class TaskTemplateConfig(BaseConfig):
    """任务模板配置"""
    config_file_path = "{}/task_template.json".format(PUSH_DATA_PATH)


class TaskConfig(BaseConfig):
    """推送任务配置"""
    config_file_path = "{}/task.json".format(PUSH_DATA_PATH)

    def get_by_keyword(self, source: str, keyword: str) -> Optional[Dict[str, Any]]:
        """根据 source 和 keyword 查找任务"""
        for i in self.config:
            if i.get("source", None) == source and i.get("keyword", None) == keyword:
                return i


class TaskRecordConfig(BaseConfig):
    """推送任务记录配置"""
    config_file_path_fmt = "%s/task_record_{}.json" % PUSH_DATA_PATH

    def __init__(self, task_id: str):
        super().__init__()
        self.config_file_path = self.config_file_path_fmt.format(task_id)


class SenderConfig(BaseConfig):
    """消息通道配置"""
    config_file_path = "{}/sender.json".format(PUSH_DATA_PATH)

    def __init__(self):
        super(SenderConfig, self).__init__()
        if not os.path.exists(self.config_file_path):
            write_file(self.config_file_path, json.dumps([{
                "id": self.nwe_id(),
                "used": True,
                "sender_type": "sms",
                "data": {},
                "original": True
            }]))


def load_task_template_by_config(templates: List[Dict]) -> None:
    """
    通过 传入的配置信息 执行一次模板更新操作
    @param templates: 模板内容，为一个数据列表
    @return: 报错信息，如果返回None则表示执行成功
    """

    task_template_config = TaskTemplateConfig()
    add_list = []
    for template in templates:
        tmp = task_template_config.get_by_id(template['id'])
        if tmp is not None:
            tmp.update(template)
        else:
            add_list.append(template)

    task_template_config.config.extend(add_list)
    task_template_config.save_config()


def load_task_template_by_file(template_file: str) -> Optional[str]:
    """
    执行一次模板更新操作
    @param template_file: 模板文件路径
    @return: 报错信息，如果返回None则表示执行成功
    """
    if not os.path.isfile(template_file):
        return "The template file does not exist and the update fails"

    res = read_file(template_file)
    if not isinstance(res, str):
        return "Data read failed"

    try:
        templates = json.loads(res)
    except (json.JSONDecoder, TypeError, ValueError):
        return "Only JSON data is supported"

    if not isinstance(templates, list):
        return "The data is in the wrong format and should be a list"

    return load_task_template_by_config(templates)

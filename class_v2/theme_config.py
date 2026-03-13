#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主题配置管理模块

该模块提供主题配置的管理功能，包括：
- 配置文件的读取、验证和保存
- 新旧版本配置格式的转换
- 配置字段的验证和默认值处理
- 配置文件状态检查和初始化

Author: aaPanel
Version: 2.0.0 (optimized)
Created: 2025-09-15
"""

import json
import os
import re
import shutil
import tarfile
import tempfile
import urllib.parse
from functools import wraps
from typing import Dict, Any, Tuple


def exception_handler(default_data=None):
    """统一异常处理装饰器"""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except json.JSONDecodeError as e:
                return self.return_message(False, f'JSON parse error: {str(e)}', default_data)
            except FileNotFoundError as e:
                return self.return_message(False, f'File not found: {str(e)}', default_data)
            except PermissionError as e:
                return self.return_message(False, f'Permission error: {str(e)}', default_data)
            except Exception as e:
                return self.return_message(False, f'{func.__name__} Error: {str(e)}', default_data)

        return wrapper

    return decorator


class FieldValidator:
    """Simplified field validator."""

    def __init__(self, field_type=None, required=False, choices=None, pattern=None, min_val=None, max_val=None):
        self.field_type = field_type
        self.required = required
        self.choices = choices
        self.pattern = re.compile(pattern) if pattern else None
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: Any) -> Tuple[bool, str]:
        """验证字段值"""
        # 检查必填字段
        if self.required and (value is None or value == ''):
            return False, 'Field is required'

        # Empty but not required: skip validation
        if value is None or value == '':
            return True, ''

        # 类型转换和验证
        if self.field_type:
            value = self._convert_type(value)
            if not isinstance(value, self.field_type):
                return False, f'Type error, expected {self.field_type.__name__}'

        # Choices validation
        if self.choices and value not in self.choices:
            return False, f'Value is not in allowed choices: {self.choices}'

        # Regex validation
        if self.pattern and isinstance(value, str) and not self.pattern.match(value):
            return False, 'Value does not match the regex pattern'

        # Range validation
        if self.min_val is not None and value < self.min_val:
            return False, f'Value is less than the minimum {self.min_val}'
        if self.max_val is not None and value > self.max_val:
            return False, f'Value is greater than the maximum {self.max_val}'

        return True, ''

    def _convert_type(self, value):
        """类型转换"""
        if self.field_type == bool and isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        elif self.field_type == int and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                pass
        return value


try:
    import public
except ImportError:
    class PublicCompat:
        @staticmethod
        def returnMsg(status, msg, data=None):
            result = {'status': status, 'msg': msg}
            if data is not None:
                result['data'] = data
            return result


    public = PublicCompat()

try:
    from BTPanel import cache
except ImportError:
    cache = None

CONFIG_FILE = '/www/server/panel/data/panel_asset.json'

class ThemeConfigManager:
    """主题配置管理器 - 优化版"""
    CACHE_KEY = "aa_theme_config_cache_v2"
    # 修复bg_image_opacity类型问题标记
    _fix_flag = '/www/server/panel/data/fix_theme_type_20260204.flag'

    # 默认配置常量
    DEFAULT_CONFIG = {
        "theme": {
            "preset": "light",
            "color": "#20a53a",
            "view": "default"
        },
        "logo": {
            "image": "/static/icons/menu_logo.png",
            "favicon": "/static/favicon.ico"
        },
        "sidebar": {
            "dark": True,
            "color": "#3c444d",
            "opacity": 100
        },
        "interface": {
            "rounded": "smaller",
            "is_show_bg": True,
            "bg_image": "/static/icons/main_bg.png",
            "bg_image_dark": "/static/icons/main_bg_dark.png",
            "bg_image_opacity": 100,
            "content_opacity": 100,
            "shadow_color": "#000000",
            "shadow_opacity": 5,
            "container_width": "100%"
        },
        "home": {
            "overview_view": "default",
            "overview_size": 24,
            "bg_image_opacity": 20
        },
        "login": {
            "is_show_logo": True,
            "logo": "/static/icons/logo-green.svg",
            "is_show_bg": False,
            "bg_image": "",
            "bg_image_opacity": 100,
            "content_opacity": 100
        },
        "terminal": {
            "show": False,
            "url": "",
            "opacity": 70
        }
    }

    # 字段验证器配置
    FIELD_VALIDATORS = {
        "theme.preset": FieldValidator(str, required=True, choices=["light", "dark"]),
        "theme.color": FieldValidator(str, required=True, pattern=r"^#[0-9a-fA-F]{3,6}$"),
        "theme.view": FieldValidator(str, required=True, choices=["default", "aapanel", "compact"]),
        "sidebar.dark": FieldValidator(bool, required=True),
        "sidebar.color": FieldValidator(str, required=True, pattern=r"^#[0-9a-fA-F]{3,6}$"),
        "sidebar.opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "interface.rounded": FieldValidator(str, required=True,
                                            choices=["none", "smaller", "small", "medium", "large"]),
        "interface.is_show_bg": FieldValidator(bool, required=True),
        "interface.bg_image_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "interface.content_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "interface.shadow_color": FieldValidator(str, required=True, pattern=r"^#[0-9a-fA-F]{3,6}$"),
        "interface.shadow_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "home.overview_view": FieldValidator(str, required=True, choices=["default", "grid", "list"]),
        "home.overview_size": FieldValidator(int, required=True, min_val=12, max_val=48),
        "login.is_show_logo": FieldValidator(bool, required=True),
        "login.is_show_bg": FieldValidator(bool, required=True),
        "login.bg_image_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "login.content_opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
        "terminal.show": FieldValidator(bool, required=True),
        "terminal.url": FieldValidator(str, required=True, pattern=r"^(?!\s*$).+"),
        "terminal.opacity": FieldValidator(int, required=True, min_val=0, max_val=100),
    }

    # 旧版本字段映射
    LEGACY_MAPPING = {
        "favicon": "logo.favicon",
        "dark": "theme.preset",  # 旧的dark字段映射到新的preset字段
        "show_login_logo": "login.is_show_logo",
        "show_login_bg_images": "login.is_show_bg",
        "login_logo": "login.logo",
        "login_bg_images": "login.bg_image",
        "login_bg_images_opacity": "login.bg_image_opacity",
        "login_content_opacity": "login.content_opacity",
        "show_main_bg_images": "interface.is_show_bg",
        "main_bg_images": "interface.bg_image",
        "main_bg_images_dark": "interface.bg_image_dark",
        "main_bg_images_opacity": "interface.bg_image_opacity",
        "main_content_opacity": "interface.content_opacity",
        "main_shadow_color": "interface.shadow_color",
        "main_shadow_opacity": "interface.shadow_opacity",
        "menu_logo": "logo.image",
        "menu_bg_opacity": "sidebar.opacity",
        "sidebar_opacity": "sidebar.opacity",
        "theme_color": "sidebar.color",
        "home_state_font_size": "home.overview_size",
    }

    @staticmethod
    def return_message(status, msg, data=None):
        """统一的消息返回函数"""
        return {
            "msg": msg,
            "data": data if data is not None else {},
            "status": status
        }

    @staticmethod
    def clean_cahce():
        def decorator(func):
            @wraps(func)
            def wrap(self, *args, **kwargs):
                if cache:
                    cache.delete(self.CACHE_KEY)
                return func(self, *args, **kwargs)
            return wrap
        return decorator

    def __init__(self, config_file_path=CONFIG_FILE, auto_init=True):
        """初始化主题配置管理器"""
        self.config_file_path = config_file_path
        self.config_dir = os.path.dirname(self.config_file_path)
        self._path_cache = {}  # 路径缓存
        self.__one_time_fix() # 修复类型

        # 可选的自动初始化配置文件
        if auto_init:
            self._ensure_config_file()

    def __one_time_fix(self):
        # 修复bg_image_opacity类型问题
        if os.path.exists(self._fix_flag):
            return
        try:
            config_content = public.readFile(CONFIG_FILE)
            if config_content:
                config_data = None
                try:
                    config_data = json.loads(config_content)
                except:
                    public.ExecShell("rm -f {}".format(CONFIG_FILE))
                if config_data.get("login", {}).get("bg_image_opacity"):
                    if not isinstance(config_data["login"]["bg_image_opacity"], int):
                        bg_image_opacity = config_data["login"]["bg_image_opacity"]
                        config_data["login"]["bg_image_opacity"] = int(bg_image_opacity)
                        public.writeFile(CONFIG_FILE, json.dumps(config_data, ensure_ascii=False, indent=2))
        except:
            public.ExecShell("rm -f {}".format(CONFIG_FILE))
        finally:
            public.writeFile(self._fix_flag, "1")

    def _split_path(self, path: str) -> list:
        """分割路径并缓存结果"""
        if path not in self._path_cache:
            self._path_cache[path] = path.split('.')
        return self._path_cache[path]

    def _get_nested_value(self, data, path, default=None):
        """获取嵌套字典的值"""
        if not isinstance(data, dict):
            return default

        keys = self._split_path(path)
        current = data

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError, AttributeError):
            return default

    def _set_nested_value(self, data, path, value):
        """设置嵌套字典的值"""
        keys = self._split_path(path)
        current = data

        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _is_legacy_format(self, config):
        """检查配置是否为旧版本格式"""
        legacy_fields = set(self.LEGACY_MAPPING.keys())
        new_structure_keys = set(self.DEFAULT_CONFIG.keys())
        config_keys = set(config.keys())

        has_legacy_fields = bool(legacy_fields.intersection(config_keys))
        has_new_structure = bool(new_structure_keys.intersection(config_keys))
        return has_legacy_fields and not has_new_structure

    def _ensure_config_file(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_file_path):
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)

    def validate_field(self, field_path: str, value: Any) -> Dict[str, Any]:
        """验证单个字段的值"""
        try:
            validator = self.FIELD_VALIDATORS.get(field_path)
            if not validator:
                return self.return_message(True, 'Field validation passed', {'value': value})

            is_valid, error_msg = validator.validate(value)
            if not is_valid:
                return self.return_message(False, f'Field {field_path} {error_msg}')

            return self.return_message(True, 'Field validation passed', {'value': value})

        except Exception as e:
            return self.return_message(False, f"Field validation error: {str(e)}")

    def detect_missing_fields(self, config):
        """检测配置中缺失的必要字段"""
        try:
            if not isinstance(config, dict):
                return self.return_message(False, 'Config must be a dict')

            missing_fields = []

            def _check_nested_fields(default_dict, current_dict, path_prefix=''):
                """递归检查嵌套字段"""
                for key, default_value in default_dict.items():
                    current_path = f"{path_prefix}.{key}" if path_prefix else key

                    if key not in current_dict:
                        missing_fields.append({
                            'path': current_path,
                            'default_value': default_value,
                            'type': type(default_value).__name__
                        })
                    elif isinstance(default_value, dict) and isinstance(current_dict.get(key), dict):
                        _check_nested_fields(default_value, current_dict[key], current_path)

            _check_nested_fields(self.DEFAULT_CONFIG, config)

            return self.return_message(True, f'Detected {len(missing_fields)} missing fields', {
                'missing_fields': missing_fields,
                'total_missing': len(missing_fields)
            })

        except Exception as e:
            return self.return_message(False, f'Missing-field detection error: {str(e)}')

    def auto_fill_missing_fields(self, config):
        """自动补充配置中缺失的必要字段"""
        try:
            if not isinstance(config, dict):
                return self.return_message(False, 'Config must be a dict')

            import copy
            filled_config = copy.deepcopy(config)
            filled_count = 0
            filled_fields = []

            def _fill_nested_fields(default_dict, current_dict, path_prefix=''):
                """递归填充嵌套字段"""
                nonlocal filled_count

                for key, default_value in default_dict.items():
                    current_path = f"{path_prefix}.{key}" if path_prefix else key

                    if key not in current_dict:
                        # 缺失字段，进行补充
                        current_dict[key] = copy.deepcopy(default_value)
                        filled_count += 1
                        filled_fields.append({
                            'path': current_path,
                            'value': default_value,
                            'type': type(default_value).__name__
                        })
                    elif isinstance(default_value, dict):
                        # 确保当前字段也是字典类型
                        if not isinstance(current_dict.get(key), dict):
                            current_dict[key] = {}
                        _fill_nested_fields(default_value, current_dict[key], current_path)

            _fill_nested_fields(self.DEFAULT_CONFIG, filled_config)

            message = f'Successfully filled {filled_count} missing fields' if filled_count > 0 else 'No fields to fill'

            return self.return_message(True, message, {
                'config': filled_config,
                'filled_fields': filled_fields,
                'filled_count': filled_count
            })

        except Exception as e:
            return self.return_message(False, f'Auto-fill error: {str(e)}')

    def validate_config(self, config):
        """验证配置数据"""
        try:
            import copy
            validated_config = copy.deepcopy(config)

            # 补充缺失的顶级字段
            missing_count = 0
            for key, default_value in self.DEFAULT_CONFIG.items():
                if key not in validated_config:
                    validated_config[key] = copy.deepcopy(default_value)
                    missing_count += 1

            # 验证关键字段
            critical_fields = ['theme.color', 'theme.view', 'sidebar.color']
            validation_fix_count = 0

            for field_path in critical_fields:
                value = self._get_nested_value(validated_config, field_path)
                if value is not None:
                    validation_result = self.validate_field(field_path, value)
                    if not validation_result["status"]:
                        default_value = self._get_nested_value(self.DEFAULT_CONFIG, field_path)
                        if default_value is not None:
                            self._set_nested_value(validated_config, field_path, default_value)
                            validation_fix_count += 1

            # 构建返回消息
            message_parts = []
            if missing_count > 0:
                message_parts.append(f'Filled {missing_count} missing top-level fields')
            if validation_fix_count > 0:
                message_parts.append(f'Fixed {validation_fix_count} validation errors')
            if not message_parts:
                message_parts.append('Config validation passed')

            return self.return_message(True, ", ".join(message_parts), validated_config)

        except Exception as e:
            return self.return_message(False, f'Config validation error: {str(e)}', self.DEFAULT_CONFIG)

    def convert_legacy_config(self, legacy_config):
        """将旧版本配置转换为新版本配置"""
        try:
            if not isinstance(legacy_config, dict):
                return self.return_message(False, 'Legacy config must be a dict')

            import copy
            new_config = copy.deepcopy(self.DEFAULT_CONFIG)
            converted_count = 0

            for old_field, new_path in self.LEGACY_MAPPING.items():
                if old_field in legacy_config:
                    value = legacy_config[old_field]
                    if not (isinstance(value, str) and value.strip().lower() == "undefined"):
                        # 特殊处理 dark 字段到 preset 字段的转换
                        if old_field == "dark" and new_path == "theme.preset":
                            # 将布尔值转换为对应的预设字符串
                            if isinstance(value, bool):
                                preset_value = "dark" if value else "light"
                            elif isinstance(value, str):
                                # 处理字符串形式的布尔值
                                preset_value = "dark" if value.lower() in ['true', '1', 'yes', 'on'] else "light"
                            else:
                                # 默认为 light
                                preset_value = "light"
                            self._set_nested_value(new_config, new_path, preset_value)
                        else:
                            # 普通字段直接设置
                            self._set_nested_value(new_config, new_path, value)
                        converted_count += 1

            return self.return_message(True, f'Successfully converted {converted_count} config items', new_config)

        except Exception as e:
            return self.return_message(False, f'Config conversion error: {str(e)}')

    def get_legacy_format_config(self):
        """获取旧版本格式的配置"""
        try:
            get_result = self.get_config()
            if not get_result['status']:
                return self.return_message(False, f'Failed to get current config: {get_result["msg"]}')

            new_config = get_result['data']
            legacy_config = {}
            converted_count = 0

            for old_field, new_path in self.LEGACY_MAPPING.items():
                value = self._get_nested_value(new_config, new_path)
                if value is not None:
                    legacy_config[old_field] = value
                    converted_count += 1

            return self.return_message(True, f'Successfully converted {converted_count} items to legacy format',
                                       legacy_config)

        except Exception as e:
            return self.return_message(False, f'Legacy-format conversion error: {str(e)}')

    def check_config_file_status(self):
        """检查配置文件状态"""
        try:
            status_info = {
                'file_path': self.config_file_path,
                'exists': os.path.exists(self.config_file_path),
                'directory_exists': os.path.exists(self.config_dir),
                'is_readable': False,
                'is_writable': False,
                'file_size': 0,
                'is_valid_json': False
            }

            if not status_info['exists']:
                if status_info['directory_exists']:
                    status_info['is_writable'] = os.access(self.config_dir, os.W_OK)
                return self.return_message(True, 'Config file status check completed', status_info)

            # Check when file exists
            status_info['is_readable'] = os.access(self.config_file_path, os.R_OK)
            status_info['is_writable'] = os.access(self.config_file_path, os.W_OK)
            status_info['file_size'] = os.path.getsize(self.config_file_path)

            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                status_info['is_valid_json'] = True
            except (json.JSONDecodeError, IOError):
                status_info['is_valid_json'] = False

            return self.return_message(True, 'Config file status check completed', status_info)

        except Exception as e:
            return self.return_message(False, f'Config file status check failed: {str(e)}')

    @staticmethod
    def _fix_bg_image_opacity(config_data: dict) -> dict:
        # 2026/02/04 修复类型仍然没转换的问题
        if config_data.get("login", {}).get("bg_image_opacity"):
            try:
                bg_image_opacity = config_data["login"]["bg_image_opacity"]
                config_data["login"]["bg_image_opacity"] = int(bg_image_opacity)
            except Exception as e:
                public.print_log(f"them conf manager error: field 'bg_image_opacity' error : {e}")
        return config_data

    @exception_handler(default_data=None)
    def get_config(self):
        """获取当前的主题配置"""
        if cache:
            cached_config = cache.get(self.CACHE_KEY)
            if cached_config and isinstance(cached_config, dict):
                return self.return_message(True, 'Config fetched from cache', cached_config)
        try:
            # 读取配置文件
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.return_message(True, 'Using default config', self.DEFAULT_CONFIG)

        # 处理旧版本配置

        if isinstance(config_data, dict):  # 移除aa弃用字段
            config_data.pop("theme_name", None)

        if self._is_legacy_format(config_data):
            convert_result = self.convert_legacy_config(config_data)
            if convert_result['status']:
                public.print_log("Update aaPanel asset config successfully!")
                config_data = convert_result['data']
                # 保存转换后的配置
                self.save_config(config_data, skip_validation=True)

        # 检查并补充 theme.preset 字段
        config_data = self._ensure_preset_field(config_data)

        # 验证并补充配置
        validation_result = self.validate_config(config_data)
        if validation_result['status']:
            validated_config = validation_result['data']

            # 兼容代码：当暗色主题使用旧版默认背景图时，禁用背景显示
            if (validated_config.get('theme', {}).get('preset') == 'dark' and
                    validated_config.get('interface', {}).get('bg_image') == '/static/images/bg-default.png'):
                validated_config['interface']['is_show_bg'] = False

            # 如果配置有变更，保存更新
            if self._config_has_changes(config_data, validated_config):
                self.save_config(validated_config, skip_validation=True)
            if cache:
                cache.set(self.CACHE_KEY, validated_config, 3600 * 24)
            return self.return_message(True, f'Config fetched successfully, {validation_result["msg"]}',
                                       validated_config)
        return self.return_message(False, validation_result['msg'], self.DEFAULT_CONFIG)

    def _config_has_changes(self, original_config, new_config):
        """检测配置是否发生了实际变更"""
        try:
            original_json = json.dumps(original_config, sort_keys=True, ensure_ascii=False)
            new_json = json.dumps(new_config, sort_keys=True, ensure_ascii=False)
            return original_json != new_json
        except Exception:
            return True

    def _ensure_preset_field(self, config):
        """确保theme.preset字段存在，如果不存在则使用theme.dark进行补充，然后移除旧版的dark字段"""
        try:
            import copy
            config_copy = copy.deepcopy(config)

            # 确保theme字段存在
            if 'theme' not in config_copy:
                config_copy['theme'] = {}

            # 检查preset字段是否存在
            if 'preset' not in config_copy['theme'] or config_copy['theme']['preset'] is None:
                # 检查是否存在dark字段
                if 'dark' in config_copy['theme']:
                    dark_value = config_copy['theme']['dark']
                    # 将dark字段转换为preset字段
                    if isinstance(dark_value, bool):
                        config_copy['theme']['preset'] = "dark" if dark_value else "light"
                    elif isinstance(dark_value, str):
                        # 处理字符串形式的布尔值
                        config_copy['theme']['preset'] = "dark" if dark_value.lower() in ['true', '1', 'yes',
                                                                                          'on'] else "light"
                    else:
                        # 默认为light
                        config_copy['theme']['preset'] = "light"
                else:
                    # 如果dark字段也不存在，使用默认值
                    config_copy['theme']['preset'] = "light"

            # 移除旧版的dark字段（如果存在）
            if 'dark' in config_copy['theme']:
                del config_copy['theme']['dark']

            return config_copy

        except Exception:
            # 如果处理过程中出现异常，返回原配置
            return config

    @clean_cahce()
    def save_config(self, config, skip_validation=False):
        """保存配置到文件"""
        try:
            if not config:
                return self.return_message(False, 'Config data cannot be empty')

            if isinstance(config, str):
                config = json.loads(config)

            # 检测并修复缺失的字段
            missing_check = self.detect_missing_fields(config)
            if missing_check['status'] and missing_check['data']['total_missing'] > 0:
                fill_result = self.auto_fill_missing_fields(config)
                if fill_result['status']:
                    config = fill_result['data']['config']

            if not skip_validation:
                validation_result = self.validate_config(config)
                if not validation_result["status"]:
                    return self.return_message(False, f'Config validation failed: {validation_result["msg"]}',
                                               validation_result.get("data", {}))
                config_to_save = validation_result["data"]
            else:
                config_to_save = config

            os.makedirs(self.config_dir, exist_ok=True)

            # 2026/02/04 修复保存时bg_image_opacity类型问题
            config_to_save = self._fix_bg_image_opacity(config_to_save)

            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)

            return self.return_message(True, 'Config saved successfully', config_to_save)

        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            return self.return_message(False, f'Config save failed: {str(e)}')

    @clean_cahce()
    def update_config(self, updates):
        """更新配置"""
        try:
            if not isinstance(updates, dict):
                return self.return_message(False, 'Update data must be a dict')

            get_result = self.get_config()
            if not get_result['status']:
                return self.return_message(False, f'Failed to get current config: {get_result["msg"]}')

            current_config = get_result['data']

            # 应用更新
            for field_path, value in updates.items():
                # 检查是否为旧版本字段名
                if field_path in self.LEGACY_MAPPING:
                    field_path = self.LEGACY_MAPPING[field_path]

                self._set_nested_value(current_config, field_path, value)

            # 保存更新后的配置
            save_result = self.save_config(current_config)
            if save_result['status']:
                return self.return_message(True, 'Config updated successfully', save_result['data'])
            else:
                return self.return_message(False, f'Config save failed: {save_result["msg"]}',
                                           save_result.get('data', {}))

        except Exception as e:
            return self.return_message(False, f'Config update failed: {str(e)}')

    @clean_cahce()
    def initialize_config_file(self, force=False):
        """手动初始化配置文件"""
        try:
            if os.path.exists(self.config_file_path) and not force:
                return self.return_message(True, 'Config file already exists; no initialization needed')

            os.makedirs(self.config_dir, exist_ok=True)

            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)

            action = 'reinitialized' if force else 'initialized'
            return self.return_message(True, f'Config file {action}; default config created', self.DEFAULT_CONFIG)

        except Exception as e:
            return self.return_message(False, f'Config file initialization failed: {str(e)}')

    # 导入/导出
    def _get_path_fields(self, config):
        """获取配置中所有包含路径的字段"""
        path_fields = []

        def _extract_paths(data, prefix=''):
            """递归提取路径字段"""
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, str) and self._is_path_field(key, value):
                        path_fields.append({
                            'field_path': current_path,
                            'value': value,
                            'is_local': self._is_local_path(value)
                        })
                    elif isinstance(value, dict):
                        _extract_paths(value, current_path)

        _extract_paths(config)
        return path_fields

    def _is_path_field(self, field_name, value):
        """判断字段是否为路径字段"""
        path_indicators = ['image', 'logo', 'favicon', 'bg_image']
        return any(indicator in field_name.lower() for indicator in path_indicators) and isinstance(value,
                                                                                                    str) and value.strip()

    def _is_local_path(self, path):
        """判断是否为本地路径（非URL）"""
        if not path or not isinstance(path, str):
            return False

        # 检查是否为URL
        parsed = urllib.parse.urlparse(path)
        if parsed.scheme in ['http', 'https', 'ftp', 'ftps']:
            return False

        # 检查是否为相对路径或绝对路径
        return path.startswith('/') or not parsed.scheme

    def _get_full_path(self, relative_path, base_path=None):
        """获取完整的文件路径"""
        if not relative_path or not isinstance(relative_path, str):
            return None

        # 自动检测基础路径
        if base_path is None:
            # 优先使用生产环境路径
            production_base = '/www/server/panel/BTPanel'
            # 如果生产环境路径不存在，使用当前项目路径
            if not os.path.exists(production_base):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                base_path = os.path.join(project_root, 'BTPanel')
            else:
                base_path = production_base

        # 如果是系统绝对路径（不以/static开头），直接返回
        if os.path.isabs(relative_path) and not relative_path.startswith('/static'):
            return relative_path

        # 移除开头的斜杠并拼接基础路径
        clean_path = relative_path.lstrip('/')
        return os.path.join(base_path, clean_path)

    def _copy_file_to_temp(self, source_path, temp_dir, relative_path):
        """复制文件到临时目录"""
        try:
            if not os.path.exists(source_path):
                return False, f'Source file does not exist: {source_path}'

            target_path = os.path.join(temp_dir, relative_path.lstrip('/'))
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)

            # 复制文件
            # noinspection PyTypeChecker
            shutil.copy2(source_path, target_path)
            return True, target_path

        except Exception as e:
            return False, f'File copy failed: {str(e)}'

    @exception_handler(default_data=None)
    def export_theme_config(self, export_path=None):
        """导出主题配置和相关文件"""
        try:
            # 获取当前配置
            config_result = self.get_config()
            if not config_result['status']:
                return self.return_message(False, f'Failed to get config: {config_result["msg"]}')

            config = config_result['data']

            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix='theme_export_')

            try:
                # 获取所有路径字段
                path_fields = self._get_path_fields(config)
                copied_files = []
                skipped_files = []

                # 复制本地路径的文件
                for field_info in path_fields:
                    if field_info['is_local']:
                        source_path = self._get_full_path(field_info['value'])
                        if source_path and os.path.exists(source_path):
                            success, result = self._copy_file_to_temp(
                                source_path, temp_dir, field_info['value']
                            )
                            if success:
                                copied_files.append({
                                    'field': field_info['field_path'],
                                    'original_path': field_info['value'],
                                    'source_path': source_path,
                                    'target_path': result
                                })
                            else:
                                skipped_files.append({
                                    'field': field_info['field_path'],
                                    'path': field_info['value'],
                                    'reason': result
                                })
                        else:
                            skipped_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value'],
                                'reason': 'File does not exist'
                            })
                    else:
                        skipped_files.append({
                            'field': field_info['field_path'],
                            'path': field_info['value'],
                            'reason': 'URL, skipped'
                        })

                # 复制配置文件
                config_target = os.path.join(temp_dir, 'panel_asset.json')
                with open(config_target, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                # 获取实际使用的基础路径
                actual_base_path = self._get_full_path('static').replace('/static', '') if self._get_full_path(
                    'static') else '/www/server/panel/BTPanel'

                # 创建导出信息文件
                export_info = {
                    'export_time': __import__('datetime').datetime.now().isoformat(),
                    'config_file': 'panel_asset.json',
                    'copied_files': copied_files,
                    'skipped_files': skipped_files,
                    'total_files': len(copied_files),
                    'base_path': actual_base_path
                }

                info_file = os.path.join(temp_dir, 'export_info.json')
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(export_info, f, ensure_ascii=False, indent=2)

                # 打包文件
                if not export_path:
                    export_path = '/tmp/panel_theme.tar.gz'
                    # 如果文件已存在，先删除旧文件
                    if os.path.exists(export_path):
                        os.remove(export_path)

                with tarfile.open(export_path, 'w:gz') as tar:
                    tar.add(temp_dir, arcname='theme_config')

                return self.return_message(True,
                                           f'Theme config exported successfully; copied {len(copied_files)} files', {
                                               'export_path': export_path,
                                               'export_info': export_info
                                           })

            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

        except Exception as e:
            return self.return_message(False, f'Export failed: {str(e)}')

    @exception_handler(default_data=None)
    def import_theme_config(self, import_file_path, backup_existing=True):
        """导入主题配置和相关文件"""
        try:
            if not os.path.exists(import_file_path):
                return self.return_message(False, 'Import file does not exist')

            if not tarfile.is_tarfile(import_file_path):
                return self.return_message(False, 'Import file is not a valid tar.gz')

            temp_dir = tempfile.mkdtemp(prefix='theme_import_')

            try:
                # 解压文件
                with tarfile.open(import_file_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)

                # 查找解压后的主目录
                extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                if not extracted_dirs:
                    return self.return_message(False, 'No valid config directory found in the archive')

                config_dir = os.path.join(temp_dir, extracted_dirs[0])

                # 检查必要文件
                config_file = os.path.join(config_dir, 'panel_asset.json')
                info_file = os.path.join(config_dir, 'export_info.json')

                if not os.path.exists(config_file):
                    return self.return_message(False, 'panel_asset.json not found in the import file')

                with open(config_file, 'r', encoding='utf-8') as f:
                    import_config = json.load(f)

                # 读取导出信息（如果存在）
                export_info = {}
                if os.path.exists(info_file):
                    with open(info_file, 'r', encoding='utf-8') as f:
                        export_info = json.load(f)

                # 备份现有配置
                backup_path = None
                if backup_existing and os.path.exists(self.config_file_path):
                    backup_path = f'{self.config_file_path}.backup_{__import__("time").strftime("%Y%m%d_%H%M%S")}'
                    shutil.copy2(self.config_file_path, backup_path)

                # 恢复文件
                restored_files = []
                failed_files = []
                # 使用动态基础路径检测
                base_path = self._get_full_path('static').replace('/static', '') if self._get_full_path(
                    'static') else '/www/server/panel/BTPanel'

                # 获取导入配置中的路径字段
                path_fields = self._get_path_fields(import_config)

                for field_info in path_fields:
                    if field_info['is_local']:
                        # 构建源文件路径（在临时目录中）
                        source_file = os.path.join(config_dir, field_info['value'].lstrip('/'))

                        if os.path.exists(source_file):
                            # 构建目标路径
                            target_path = self._get_full_path(field_info['value'], base_path)

                            try:
                                # 创建目标目录
                                target_dir = os.path.dirname(target_path)
                                os.makedirs(target_dir, exist_ok=True)

                                # 复制文件
                                shutil.copy2(source_file, target_path)
                                restored_files.append({
                                    'field': field_info['field_path'],
                                    'path': field_info['value'],
                                    'target': target_path
                                })

                            except Exception as e:
                                failed_files.append({
                                    'field': field_info['field_path'],
                                    'path': field_info['value'],
                                    'error': str(e)
                                })
                        else:
                            failed_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value'],
                                'error': 'File not present in import archive'
                            })

                # 保存配置
                save_result = self.save_config(import_config)
                if not save_result['status']:
                    # 如果保存失败，恢复备份
                    if backup_path and os.path.exists(backup_path):
                        shutil.copy2(backup_path, self.config_file_path)
                    return self.return_message(False, f'Config save failed: {save_result["msg"]}')

                return self.return_message(True,
                                           f'Theme config imported successfully; restored {len(restored_files)} files',
                                           {
                                               'restored_files': restored_files,
                                               'failed_files': failed_files,
                                               'backup_path': backup_path,
                                               'export_info': export_info
                                           })

            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

        except Exception as e:
            return self.return_message(False, f'Import failed: {str(e)}')

    def validate_theme_file(self, import_file_path):
        """验证导入文件的有效性"""
        try:
            if not os.path.exists(import_file_path):
                return self.return_message(False, 'Import file does not exist')

            if not tarfile.is_tarfile(import_file_path):
                return self.return_message(False, 'File is not a valid tar.gz')

            temp_dir = tempfile.mkdtemp(prefix='theme_validate_')

            try:
                # 解压文件进行验证
                with tarfile.open(import_file_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)

                # 查找解压后的主目录
                extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                if not extracted_dirs:
                    return self.return_message(False, 'No valid config directory found in the archive')

                config_dir = os.path.join(temp_dir, extracted_dirs[0])

                # 检查必要文件
                config_file = os.path.join(config_dir, 'panel_asset.json')
                info_file = os.path.join(config_dir, 'export_info.json')

                if not os.path.exists(config_file):
                    return self.return_message(False, 'panel_asset.json not found in the archive')

                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        import_config = json.load(f)
                except json.JSONDecodeError:
                    return self.return_message(False, 'Invalid config file format')

                export_info = {}
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            export_info = json.load(f)
                    except json.JSONDecodeError:
                        pass  # 导出信息文件可选

                # 验证配置结构
                validation_result = self.validate_config(import_config)
                if not validation_result['status']:
                    return self.return_message(False, f'Config validation failed: {validation_result["msg"]}')

                path_fields = self._get_path_fields(import_config)
                available_files = []
                missing_files = []

                for field_info in path_fields:
                    if field_info['is_local']:
                        source_file = os.path.join(config_dir, field_info['value'].lstrip('/'))
                        if os.path.exists(source_file):
                            file_size = os.path.getsize(source_file)
                            available_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value'],
                                'size': file_size
                            })
                        else:
                            missing_files.append({
                                'field': field_info['field_path'],
                                'path': field_info['value']
                            })

                return self.return_message(True, 'Import file validation passed', {
                    'config': import_config,
                    'export_info': export_info,
                    'available_files': available_files,
                    'missing_files': missing_files,
                    'total_available': len(available_files),
                    'total_missing': len(missing_files)
                })

            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

        except Exception as e:
            return self.return_message(False, f'Validation failed: {str(e)}')

    def get_export_file_info(self, export_file_path):
        """获取导出文件的详细信息"""
        try:
            if not os.path.exists(export_file_path):
                return self.return_message(False, 'File does not exist')

            file_info = {
                'file_path': export_file_path,
                'file_size': os.path.getsize(export_file_path),
                'is_valid_tar': tarfile.is_tarfile(export_file_path)
            }

            if not file_info['is_valid_tar']:
                return self.return_message(False, 'Not a valid tar.gz', file_info)

            with tarfile.open(export_file_path, 'r:gz') as tar:
                file_info['contents'] = tar.getnames()
                file_info['total_files'] = len(file_info['contents'])

            # 验证文件内容
            validation_result = self.validate_theme_file(export_file_path)
            if validation_result['status']:
                file_info.update(validation_result['data'])

            return self.return_message(True, 'File info fetched successfully', file_info)

        except Exception as e:
            return self.return_message(False, f'Failed to get file info: {str(e)}')

    def test_path_detection(self):
        """测试路径检测和文件存在性检查"""
        try:
            # 获取当前配置
            config_result = self.get_config()
            if not config_result['status']:
                return self.return_message(False, f'Failed to get config: {config_result["msg"]}')

            config = config_result['data']

            # 检测基础路径
            base_path = self._get_full_path('static').replace('/static', '') if self._get_full_path(
                'static') else '/www/server/panel/BTPanel'

            # 获取所有路径字段
            path_fields = self._get_path_fields(config)

            test_results = {
                'base_path': base_path,
                'base_path_exists': os.path.exists(base_path),
                'path_fields': [],
                'summary': {
                    'total_fields': len(path_fields),
                    'local_fields': 0,
                    'url_fields': 0,
                    'existing_files': 0,
                    'missing_files': 0
                }
            }

            for field_info in path_fields:
                field_result = {
                    'field_path': field_info['field_path'],
                    'value': field_info['value'],
                    'is_local': field_info['is_local'],
                    'full_path': None,
                    'exists': False
                }

                if field_info['is_local']:
                    test_results['summary']['local_fields'] += 1
                    full_path = self._get_full_path(field_info['value'])
                    field_result['full_path'] = full_path
                    if full_path and os.path.exists(full_path):
                        field_result['exists'] = True
                        test_results['summary']['existing_files'] += 1
                    else:
                        test_results['summary']['missing_files'] += 1
                else:
                    test_results['summary']['url_fields'] += 1

                test_results['path_fields'].append(field_result)

            return self.return_message(True, 'Path detection test completed', test_results)

        except Exception as e:
            return self.return_message(False, f'Path detection test failed: {str(e)}')

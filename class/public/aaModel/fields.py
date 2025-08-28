# coding: utf-8
import itertools
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from typing import Any, TypeVar, List, Optional

from public.exceptions import HintException

__all__ = [
    "StrField",
    "IntField",
    "FloatField",
    "BlobField",
    "ListField",
    "DictField",
    "DateTimeStrField",
]

M = TypeVar("M", bound="aaModel")


def json_func(v_type: type, value: Any, forward: bool = True):
    try:
        if forward is True:
            if isinstance(value, v_type):
                return json.dumps(value)
        else:
            if isinstance(value, str):
                return json.loads(value)
        return value
    except TypeError as t:
        print("type error %s" % t)
        return value
    except Exception as e:
        print("error %s" % e)
        raise e


def marks_dirty(func: Callable) -> Callable:
    """脏 wrapper"""

    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, "_mark_dirty"):
            self._mark_dirty()
        return result

    return wrapper


class TrackedList(list):
    """override list, track fields dirty"""
    __slots__ = ("_tracker", "_field_name", "_batch")

    def __init__(self, *args, tracker=None, field_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._tracker = tracker
        self._field_name = field_name
        self._batch = False

    def _mark_dirty(self):
        if self._tracker and self._field_name and self._batch is False:
            self._tracker._mark_dirty(self._field_name)

    @marks_dirty
    def append(self, item):
        super().append(item)

    @marks_dirty
    def remove(self, item):
        super().remove(item)

    @marks_dirty
    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    @marks_dirty
    def pop(self, *args, **kwargs):
        return super().pop(*args, **kwargs)

    @marks_dirty
    def clear(self):
        super().clear()

    def extend(self, iterable):
        self._batch = True
        try:
            super().extend(iterable)
        finally:
            self._batch = False
            self._mark_dirty()


class TrackedDict(dict):
    """override dict, track fields dirty"""
    __slots__ = ("_tracker", "_field_name", "_batch")

    def __init__(self, *args, tracker=None, field_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._tracker = tracker
        self._field_name = field_name
        self._batch = False

    def _mark_dirty(self):
        if self._tracker and self._field_name and self._batch is False:
            self._tracker._mark_dirty(self._field_name)

    @marks_dirty
    def __setitem__(self, key, value):
        super().__setitem__(key, value)

    @marks_dirty
    def __delitem__(self, key):
        super().__delitem__(key)

    @marks_dirty
    def pop(self, key, *args, **kwargs):
        return super().pop(key, *args, **kwargs)

    @marks_dirty
    def clear(self):
        super().clear()

    def update(self, *args, **kwargs):
        self._batch = True
        try:
            # noinspection PyArgumentList
            super().update(*args, **kwargs)
        finally:
            self._batch = False
            self._mark_dirty()


@dataclass
class aaField(object):
    """
    字段基类
    default     默认值
    ps          字段说明
    null        是否null
    primary_key 是否主键
    foreign_key 外键
    field_name  字段key
    field_type  sql类型
    py_type     py类型
    compare     比较
    transform    转换工具
    """
    default: Any = None
    ps: str = None
    null: bool = False
    primary_key: bool = False
    field_name: str = None
    field_type: str = None
    py_type: type = None
    compare: tuple = None
    serialized: Callable = None

    def __set_name__(self, owner: M, name: str):
        self.__model = owner
        self.field_name = str(name)

    def __get__(self, instance: object, owner):
        if instance is None:
            return self
        try:
            return instance.__dict__[self.field_name]
        except KeyError:
            raise AttributeError(f'{self.field_name} is not set')

    def __set__(self, instance: M, value: Any):
        # base type field, check new set value
        if self.field_name not in instance.__dict__ or instance.__dict__[self.field_name] != value:
            instance.__dict__[self.field_name] = value
            if hasattr(instance, "_mark_dirty"):
                instance._mark_dirty(self.field_name)

    def __delete__(self, instance):
        try:
            del instance.__dict__[self.field_name]
        except KeyError:
            raise AttributeError(f"{instance} dont have attr '{self.field_name}'")

    def _raise_error(self, raise_exp: bool = True) -> bool:
        if raise_exp is True:
            err = f"'{self.field_name}' TypeError! It should be '{self.py_type.__name__}'"
            raise HintException(err)
        else:
            return False

    def _check_type(self, target: Any, raise_exp=True) -> Optional[bool]:
        target = target if not isinstance(target, Callable) else target()
        if any(isinstance(target, x) for x in self.py_types):
            return True
        return self._raise_error(raise_exp=raise_exp)

    @property
    def default_val_sql(self) -> str:
        default_v = self.get_default_val(check=True)
        default_v = default_v if self.serialized is None else self.serialized(default_v)
        return f"DEFAULT '{default_v}'" if isinstance(default_v, str) else f"DEFAULT {default_v}"

    @property
    def py_types(self) -> List[type]:
        if self.null is True:
            original = [type(self.default), self.py_type, type(None)]
        else:
            original = [type(self.default), self.py_type]
        return list(set(original))

    def get_default_val(self, check: bool = False) -> Optional[Any]:
        if check:
            self.check_org_type(raise_exp=check)
        if self.default is not None:
            return self.default if not isinstance(self.default, Callable) else self.default()
        else:
            if self.null is True:
                return None
            else:
                raise TypeError(
                    f"\n1: field '{self.field_name}' is not null, must have a default value"
                    f"\n2: you can add the '{self.field_name}' field's params null=True"
                )

    def model_check_type(self, target: Any, raise_exp=True) -> bool:
        """
        检查模型当前类型结构
        """
        return self._check_type(target, raise_exp=raise_exp)

    def check_org_type(self, raise_exp: bool = True) -> bool:
        """
        检查初始化的类型结构
        """
        return self._check_type(self.default, raise_exp=raise_exp)


@dataclass()
class StrField(aaField):
    """
    String field

    field__like="a",
    field__ne="a",
    field__in=["a", "b", "c"]
    field__not_in=["a", "b", "c"]
    field__startswith="a"
    field__endswith="a"
    """
    default: str | None = ""
    field_type: str = "TEXT"
    py_type: type = str
    max_length: int = 255  # not limit now
    min_length: int = 0  # not limit now
    compare: tuple[str] = (
        "like",
        "ne",
        "in",
        "not_in",
        "startswith",
        "endswith",
    )


@dataclass
class IntField(aaField):
    """
    Int field

    field__gt=1,
    field__gte=1,
    field__lt=1,
    field__lte=1,
    field__ne=1,
    field__in=[1, 2, 3]
    field__not_in=[1, 2, 3]
    """
    default: int | None | Any = 0
    field_type: str = "INTEGER"
    py_type: type = int
    max: int = 0  # not limit now
    min: int = 0  # not limit now
    compare: tuple[str] = (
        "gt",
        "lt",
        "gte",
        "lte",
        "ne",
        "in",
        "not_in",
    )


@dataclass
class FloatField(aaField):
    """
    Float field
    """
    default: float | None = 0.0
    field_type: str = "REAL"
    py_type: type = float
    max: float = 0.0  # not limit now
    min: float = 0.0  # not limit now
    compare: tuple[str] = (
        "gt",
        "lt",
        "gte",
        "lte",
        "ne",
        "in",
        "not_in",
    )


@dataclass
class BlobField(aaField):
    """
    Blob field
    """
    default: bytes | None = b''
    field_type: str = "BLOB"
    py_type: type = bytes



@dataclass
class ListField(aaField):
    """
    List field
    """

    # override __get__ to return tracker
    def __get__(self, instance: M, owner):
        if instance is None:
            return self
        value = instance.__dict__.get(self.field_name, self.default or [])
        if not isinstance(value, TrackedList):
            # generate tracker
            value = TrackedList(value, tracker=instance, field_name=self.field_name)
            instance.__dict__[self.field_name] = value  # update instance's attr
        return value

    @staticmethod
    def _serialized(value: list | str, forward: bool = True) -> list | Any:
        return json_func(list, value, forward)

    default: list = dataclass_field(default_factory=list)
    field_type: str = "TEXT"
    serialized: Callable = _serialized
    py_type: type = list
    compare: tuple[str] = (
        "like",
        "contains",
        "any_contains",
    )
    update: tuple[str] = (
        "append",
    )


@dataclass
class DictField(aaField):
    """
    Dict field
    """

    def __get__(self, instance, owner):
        if instance is None:
            return self
        value = instance.__dict__.get(self.field_name, self.default or {})
        if not isinstance(value, TrackedDict):
            # generate tracker
            value = TrackedDict(value, tracker=instance, field_name=self.field_name)
            instance.__dict__[self.field_name] = value  # update instance's attr
        return value

    @staticmethod
    def _serialized(value: dict | str, forward: bool = True) -> dict | Any:
        return json_func(dict, value, forward)

    default: dict = dataclass_field(default_factory=dict)
    field_type: str = "TEXT"
    serialized: Callable = _serialized
    py_type: type = dict
    compare: tuple[str] = (
        # "has_key",
        # "has_value",
        # "has_key_value",
        "lt",
        "lte",
        "gt",
        "gte",
        "ne",
        "like",
        "startswith",
        "endswith",
    )
    update: tuple[str] = (
        "update",
    )


@dataclass
class DateTimeStrField(aaField):
    """
    时间戳
    auto_now_add=True 创建时间自动添加
    auto_now=True     更新时间自动更新
    """

    @classmethod
    def _current_timestamp(cls):
        return time.strftime(cls.format, time.localtime())

    @staticmethod
    def _dynamic(obj, val):
        if hasattr(obj, "auto_now_add") and obj.auto_now_add is True:  # 创建时间
            return val
        elif hasattr(obj, "auto_now") and obj.auto_now is True:  # 更新时间
            return obj.get_default_val()
        else:
            return val

    @staticmethod
    def _serialized(value: int | str, forward: bool = True) -> str | int:
        try:
            if forward is True:
                if isinstance(value, str):  # save will be str
                    return int(
                        datetime.strptime(value, DateTimeStrField.format).timestamp() * DateTimeStrField.accuracy)
            else:
                if isinstance(value, int):
                    return datetime.fromtimestamp(value / DateTimeStrField.accuracy).strftime(DateTimeStrField.format)
            return value
        except Exception as e:
            print("type error %s" % e)
            return value

    serialized: Callable = _serialized
    default: str | Callable = ""
    field_type: str = "INTEGER"
    py_type: type = str
    dynamic: bool = True
    auto_now_add: bool = False
    auto_now: bool = False
    accuracy: int = 1000
    format: str = "%Y-%m-%d %H:%M:%S"
    compare: tuple[str] = (
        "gt",
        "lt",
        "gte",
        "lte",
    )

    def __post_init__(self):
        if self.auto_now_add is True and self.auto_now is True:
            raise TypeError("auto_now_add and auto_now can not be used at the same time")
        if self.auto_now is True:
            self.default = self._current_timestamp
        elif self.auto_now_add is True:
            self.default = self._current_timestamp


COMPARE = tuple(set(
    itertools.chain(
        *[
            StrField.compare,
            IntField.compare,
            FloatField.compare,
            ListField.compare,
            DictField.compare,
            DateTimeStrField.compare,
        ]
    )
))

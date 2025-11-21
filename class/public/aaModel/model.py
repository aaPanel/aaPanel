# coding: utf-8

import copy
from dataclasses import replace as replace_dataclass
from functools import lru_cache
from typing import Self, Generator, Optional, Dict, Any

from .fields import aaField, COMPARE
from .manager import aaManager

__all__ = ["aaModel"]

from public.exceptions import HintException


@lru_cache(maxsize=16)
def generate_table_name(class_name: str) -> str:
    """
    驼峰名转表名
    """
    return ''.join(['_' + c.lower() if c.isupper() else c for c in class_name]).lstrip('_')


class aaMetaClass(type):
    __abstract__: bool
    __db_name__: str
    __table_name__: str
    __fields__: dict
    __primary_key__: str
    __serializes__: dict
    __index_keys__: list

    def __new__(cls, name, bases, attrs):
        if attrs.get("__abstract__") is True:
            return super().__new__(cls, name, bases, attrs)
        attrs.update({"__abstract__": False})
        new_class = super().__new__(cls, name, bases, attrs)
        cls.__fields_process(obj=new_class, name=name, attrs=attrs)
        cls.__database_process(obj=new_class, name=name, attrs=attrs)
        return new_class

    def __setattr__(cls, key, value):
        if key == '__abstract__':
            raise AttributeError("can't set attribute '__abstract__'")
        return super().__setattr__(key, value)

    @classmethod
    def __fields_process(cls, obj: "aaMetaClass", name: str, attrs: dict):
        pk = ""
        fields = {}
        for k, v in attrs.items():
            if isinstance(v, aaField):
                if k in fields:
                    raise HintException(f"model {name} field '{k}' is already defined")
                if k in COMPARE:
                    raise HintException(f"model {name} field '{k}' is compare field, please change the name")
                if k.startswith("_"):
                    raise HintException(f"model {name} field '{k}' is not support start with '_'")
                fields[k] = v
                if v.primary_key:
                    if pk:
                        raise HintException(f"model {name} can only have one primary key")
                    else:
                        pk = k
        if not pk:
            raise HintException(f"sth wrong with {name}'s primary key, please check the model")
        setattr(obj, "__primary_key__", pk)
        setattr(obj, "__fields__", fields)

    @classmethod
    def __database_process(cls, obj: "aaMetaClass", name: str, attrs: dict):
        db_name, tb_name, idx = "default", generate_table_name(name), []
        meta = attrs.get("_Meta")
        if meta:
            if hasattr(meta, "db_name"):
                db_name = meta.db_name
            if hasattr(meta, "table_name"):
                tb_name = meta.table_name
            if hasattr(meta, "index"):
                idx = meta.index
        setattr(obj, "__db_name__", db_name)
        setattr(obj, "__table_name__", tb_name)
        setattr(obj, "__index_keys__", idx)


class aaCusModel(metaclass=aaMetaClass):
    __abstract__ = True
    objects = aaManager()
    _dirty_fields: Optional[set] = None

    def __init__(self, **kwargs):
        if self.__abstract__:
            raise RuntimeError(f'{self.__class__.__name__} class can not be init')
        self._field_filter = kwargs.pop("_field_filter", None)
        for f, v in self._generate_init(kwargs, all_flag=True):
            setattr(self, f.field_name, v)
        # after init set, init dirty fields set
        self._dirty_fields = set()

    def _mark_dirty(self, field_name: str):
        if self._dirty_fields is None:
            return
        self._dirty_fields.add(field_name)

    def _generate_init(self, val_data: dict, all_flag: bool = False) -> Generator:
        fields_map = self._get_fields() if all_flag else {
            k: v for k, v in self._get_fields().items()
            if k in val_data or (hasattr(v, "dynamic") and v.auto_now is True)
        }
        for name, field in fields_map.items():
            default_val = field.get_default_val()
            val = val_data.get(name, default_val)
            if field.primary_key is True and val == 0:
                continue  # skip default id val
            if field.primary_key is True and val != 0:
                try:
                    val = int(val)
                except Exception:
                    pass
            yield field, val

        # if val_data:  # other field
        # raise AttributeError(f"model '{self.__class__.__name__}' has no field {val_data}")
        # pass

    # =========================================
    @classmethod
    @lru_cache(maxsize=32)
    def _get_fields(cls):
        return cls.__fields__

    @classmethod
    @lru_cache(maxsize=32)
    def _get_serialized(cls) -> dict:
        return {
            k: replace_dataclass(v) for k, v in cls._get_fields().items() if v.serialized is not None
        }

    @classmethod
    def _get_serialized_fields_fz(cls) -> frozenset:
        return frozenset(cls._get_serialized().keys())


class aaModel(aaCusModel):
    """
    基础模型

    :example:
    class MyTestModel(aaModel):
        id = IntField(primary_key=True)
        name = StrField(ps="名字")
        status = BoolField(default=True, ps="状态")
        float_number = FloatField(default=0.05, ps="浮点")

        class _Meta:
            db_name = "default"      默认为 default.db 文件
            table_name = "my_table"  默认为类名驼峰转表名 my_test_model
            index = ["status"]  索引

    """
    __db_name__: str
    __table_name__: str
    __fields__: dict
    __primary_key__: str
    __serializes__: dict
    __index_keys__: list

    __abstract__: bool = True
    __destroyed: bool = False
    id: int = None

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.as_dict()}>"

    @staticmethod
    def check_destroyed(func):
        def wrapper(self, *args, **kwargs):
            if getattr(self, "__destroyed", False):
                raise RuntimeError(f"Cannot call {func.__name__}() on destroyed object")
            return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    @check_destroyed
    def _output(cls, data: dict, _field_filter=None) -> dict:
        serlz = cls._get_serialized()
        serlz_fields = cls._get_serialized_fields_fz()
        if _field_filter is not None:
            data = {k: v for k, v in data.items() if k in _field_filter}

        return {
            k: serlz[k].serialized(v, False) if k in serlz_fields else v
            for k, v in data.items()
        }

    @classmethod
    @check_destroyed
    def _serialized_data(cls, data: Optional[dict | list], _field_filter=None) -> Optional[dict | list]:
        if isinstance(data, list):
            return [cls._output(d, _field_filter) for d in data]
        elif isinstance(data, dict):
            return cls._output(data, _field_filter)
        else:
            return data

    @check_destroyed
    def _validate(self, target: dict = None, raise_exp: bool = True) -> Optional[Dict[str, Any]]:
        """
        模型验证, 返回序列化后的结果
        """
        body = {}
        for f, cur_val in self._generate_init(target or copy.deepcopy(self.__dict__)):
            try:
                # 1, dynamic generated
                if hasattr(f, "dynamic") and f.dynamic is True:
                    cur_val = f._dynamic(f, cur_val)
                    setattr(self, f.field_name, cur_val)
                # 2, check type and return serialized
                if f.model_check_type(target=cur_val, raise_exp=raise_exp) is True:
                    body[f.field_name] = f.serialized(cur_val, True) if f.serialized else cur_val
                else:
                    # if not raise_exp and check is False, return {}
                    return None
            except HintException as e1:
                if raise_exp:
                    raise e1
                return None
            except Exception as e:
                raise Exception(e)
        return body

    def _before_save(self):
        # override
        pass

    def _after_save(self):
        # override
        pass

    def _before_update(self):
        # override
        pass

    def _after_update(self):
        # override
        pass

    @check_destroyed
    def save(self, raise_exp: bool = True) -> Optional[Self]:
        """
        模型数据, 不存在则 保存 , 存在则 更新, 仅更新变动字段
        :raise_exp 抛异常
        :return: model object 字段类型异常等问题返回 None
        """
        if self.__class__.__abstract__:
            raise RuntimeError(f'{self.__class__.__name__} class can not be save')
        try:
            cls = self.__class__
            primary_key = cls.__primary_key__
            pk = int(self.__dict__.get(primary_key, 0))

            # not changed & not insert.
            if not self._dirty_fields and pk != 0:
                return self

            dirtys = {
                k: v for k, v in self.__dict__.items() if k in self._dirty_fields
            }

            if pk == 0:
                # insert, all fields default
                validate = self._validate(raise_exp=raise_exp)
            else:
                if "update_time" in cls._get_fields() and "update_time" not in dirtys:
                    dirtys["update_time"] = None
                # for field_name, field_obj in cls._get_fields().items():
                #     if hasattr(field_obj, "auto_now") and field_obj.auto_now:
                #         dirtys[field_name] = None
                # update, olnly validate dirty fields
                validate = self._validate(target=dirtys, raise_exp=raise_exp)

            if not validate:
                if raise_exp:
                    raise HintException("validate error")
                return None

            if pk == 0:  # insert
                self._before_save()
                new_id = cls.objects._insert(validate)
                if not new_id:
                    if raise_exp:
                        raise HintException("insert failed")
                    return None
                self.__dict__[primary_key] = new_id
                self._after_save()
            else:  # update
                self._before_update()
                if cls.objects._update({primary_key: pk}, validate) == 1:
                    self._after_update()
                else:  # update failed
                    if raise_exp:
                        raise HintException("update failed")
                    return None
            # reset in finally block
            return self
        except (TypeError, AttributeError) as t:
            if raise_exp:
                raise t
            return None
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            raise HintException(e)
        finally:
            if self._dirty_fields:
                self._dirty_fields.clear()

    @check_destroyed
    def delete(self) -> int:
        try:
            self.__class__.objects._query.where(
                f"{self.__class__.__primary_key__}=?", (self.id,)
            ).delete()
            setattr(self, "__destroyed", True)
        except Exception as e:
            print(e)
            return 0
        return 1

    @check_destroyed
    def as_dict(self) -> dict:
        """
        转字典
        """
        result = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if self._field_filter is not None and k not in self._field_filter:
                continue
            result[k] = v
        return result

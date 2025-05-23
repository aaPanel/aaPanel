# coding: utf-8

import copy
from typing import Self, Generator, Optional, Dict, Any

from .fields import aaField, COMPARE
from .manager import aaManager

__all__ = ["aaModel"]

from public.exceptions import HintException


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

    # __foreign_keys__: object

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
        setattr(obj, "__serializes__", cls.__get_serialized(fields))

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

    @staticmethod
    def __get_serialized(fields: Dict[str, aaField]) -> Dict[str, aaField]:
        return dict(filter(
            lambda x: x[1].serialized is not None, {**fields}.items()
        ))


class aaCusModel(metaclass=aaMetaClass):
    __abstract__ = True
    objects = aaManager()

    def __init__(self, **kwargs):
        if self.__abstract__ is True:
            raise RuntimeError(f'{self.__class__.__name__} class can not be init')
        self._field_filter = kwargs.pop("_field_filter", None)
        for f, v in self._generate_init(kwargs):
            setattr(self, f.field_name, v)

    def _generate_init(self, val_data: dict) -> Generator:
        for name, field in {**self.__class__.__fields__}.items():
            val = val_data.pop(name) if name in val_data else field.get_default_val()
            if field.primary_key is True and val == 0:
                continue  # skip default id val
            if field.primary_key is True and val != 0:
                try:
                    val = int(val)
                except Exception:
                    pass
            yield field, val
        if val_data:  # other field
            # raise AttributeError(f"model '{self.__class__.__name__}' has no field {val_data}")
            pass


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
    __abstract__: bool = True
    __destroyed: bool = False
    id: int = None

    def __repr__(self):
        return f"<'{self.__class__.__name__}' Model Object, {self.as_dict()}>"

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
        if not _field_filter:
            return {
                k: v if not cls.__serializes__.get(k) else cls.__serializes__.get(k).serialized(v, False) for k, v in
                data.items()
            }
        else:
            return {
                k: v if not cls.__serializes__.get(k) else cls.__serializes__.get(k).serialized(v, False) for k, v in
                data.items() if k in _field_filter
            }

    @classmethod
    @check_destroyed
    def _serialized_data(cls, data: Optional[dict | list], _field_filter=None) -> Optional[dict | list]:
        if not data or not hasattr(cls, "__serializes__"):
            return data
        if isinstance(data, list):
            return [cls._output(d, _field_filter) for d in data]
        elif isinstance(data, dict):
            return cls._output(data, _field_filter)
        else:
            return data

    @check_destroyed
    def _validate(self, raise_exp: bool = True) -> Optional[Dict[str, Any]]:
        """
        模型验证
        """
        body = {}
        for f, cur_val in self._generate_init(copy.deepcopy(self.__dict__)):
            try:
                f.model_check_type(target=cur_val, raise_exp=True)
                # 1, dynamic generated
                if hasattr(f, "dynamic") and f.dynamic is True:
                    cur_val = f._dynamic(f, cur_val)
                    setattr(self, f.field_name, cur_val)
                # 2, serialized
                body[f.field_name] = f.serialized(cur_val, True) if f.serialized else cur_val
            except TypeError as t:
                if raise_exp:
                    raise t
                else:
                    return {}
            except Exception as e:
                raise e
        return body

    def _before_save(self) -> bool:
        # override
        return True

    def _after_save(self) -> None:
        # override
        pass

    @check_destroyed
    def save(self, raise_exp: bool = True) -> Optional[Self]:
        """
        模型数据, 不存在则 保存 , 存在则 更新
        :raise_exp 抛异常
        :return: model object 字段类型异常等问题返回 None
        """
        if self.__class__.__abstract__ is True:
            raise RuntimeError(f'{self.__class__.__name__} class can not be save')
        try:
            cls = self.__class__
            validate = self._validate(raise_exp=raise_exp)
            primary_key = cls.__primary_key__
            if validate and primary_key:
                if primary_key in validate:
                    target_id = validate.pop(primary_key)
                    exist = cls.objects._query.where(f"{primary_key}=?", (target_id,)).exists()
                    if exist:  # update
                        res = cls.objects._query.where(f"{primary_key}=?", (target_id,)).update(validate)
                        if res == 1:
                            self._after_save()
                            return self
                        else:
                            if raise_exp:
                                raise HintException("update error")
                            else:
                                return None
                    else:
                        validate[primary_key] = target_id
                # save
                if not self._before_save():
                    return None
                new_id = cls.objects._query.insert(validate)
                self._after_save()
                return cls(**{primary_key: new_id, **self.__dict__})
            return None
        except TypeError as t:
            if raise_exp:
                raise t
            else:
                return None
        except Exception as e:
            raise HintException(e)

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
        field_filter = getattr(self, "_field_filter", None)
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                continue
            if field_filter is not None and k not in field_filter:
                continue
            result[k] = v
        return result

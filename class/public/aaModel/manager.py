# coding: utf-8
import json
import uuid
from functools import reduce
from itertools import chain
from typing import Optional, TypeVar, Generic, Any, List, Dict, Generator, Iterable

import public
from public.aaModel.fields import COMPARE
from public.exceptions import HintException, PanelError
from public.sqlite_easy import Db

__all__ = ["aaManager", "Q", "QueryProperty"]

M = TypeVar("M", bound="aaModel")


def get_flag() -> bool:
    import sqlite3
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("SELECT json_extract('{\"a\": 1}', '$.a')")
        cursor.execute("SELECT COUNT(*) FROM json_each('{\"a\":1, \"b\":2}')")
        conn.close()
        return True
    except sqlite3.Error:
        return False
    except:
        return False


class QueryProperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        return self.func(owner)


class Operator:
    _shared_flag = None

    def __new__(cls, *args, **kwargs):
        if cls._shared_flag is None:
            cls._shared_flag = get_flag()
        return super().__new__(cls)

    def __init__(self, model_class: M, query: Db.query):
        self._model_class: M = model_class
        self._query = query
        self._tb = self._model_class.__table_name__
        self._fields = self._model_class.__fields__
        self._serializes = self._model_class.__serializes__
        self._flag = self._shared_flag  # fk flag

    def _q_error(self, key: str, act: str, val: Any, sp_act: tuple):
        raise HintException(
            "field: '%s' is not support '%s', you can use: %s" % (key, act, sp_act)
        )

    def _deep_equal(self, obj1: Any, obj2: Any) -> bool:
        if type(obj1) != type(obj2):
            return False
        if isinstance(obj1, dict):
            if set(obj1.keys()) != set(obj2.keys()):
                return False
            return all(self._deep_equal(obj1[k], obj2[k]) for k in obj1)
        if isinstance(obj1, list):
            if len(obj1) != len(obj2):
                return False
            return all(self._deep_equal(i1, i2) for i1, i2 in zip(obj1, obj2))
        return obj1 == obj2

    def _deep_equal_in(self, item: Any, container_list: List[Any]) -> bool:
        for elem in container_list:
            if self._deep_equal(item, elem):
                return True
        return False

    def _python_compare(self, v: Any, op_str: str, q_v: Any) -> bool:
        try:
            if op_str == "gt":
                return v > q_v
            if op_str == "lt":
                return v < q_v
            if op_str == "gte":
                return v >= q_v
            if op_str == "lte":
                return v <= q_v
            if op_str == "ne":
                return not self._deep_equal(v, q_v)

            if op_str == "like":
                return isinstance(v, str) and isinstance(q_v, str) and q_v in v
            if op_str == "startswith":
                return isinstance(v, str) and isinstance(q_v, str) and v.startswith(q_v)
            if op_str == "endswith":
                return isinstance(v, str) and isinstance(q_v, str) and v.endswith(q_v)

            if op_str == "in":
                return isinstance(q_v, list) and self._deep_equal_in(v, q_v)
            if op_str == "not_in":
                return isinstance(q_v, list) and not self._deep_equal_in(v, q_v)

            if op_str == "contains" or op_str == "any_contains":
                items_to_search = q_v
                if not isinstance(items_to_search, list):
                    items_to_search = [items_to_search]
                if not items_to_search:  # 如果搜索列表为空
                    return True if op_str == "contains" else False  # AND(empty)=True, OR(empty)=False

                match_results = []
                for item in items_to_search:
                    found = False
                    if isinstance(v, list):
                        found = self._deep_equal_in(item, v)
                    elif isinstance(v, str) and isinstance(item, str):
                        found = item in v
                    elif isinstance(v, dict):  # 检查item是否为dict中的值
                        found = self._deep_equal_in(item, list(v.values()))

                    match_results.append(found)

                return all(match_results) if op_str == "contains" else any(match_results)

        except TypeError:  # 比较不兼容的类型
            return False
        except Exception:
            return False
        return False

    def __check_js_type(self, key: str, val: Any) -> None:
        for t in [str, int]:
            if isinstance(val, t):
                break
        else:
            raise HintException(
                "%s's fields %s is not support compare value type: %s" % (self._model_class.__name__, key, val)
            )

    def __generate_road(self, road):
        path = "$"
        for r in road:
            if r.isdigit():
                path += f"[{r}]"
            else:
                path += f".{r}"
        return path

    def __is_json(self, val: Any):
        if isinstance(val, (dict, list)):
            return True, json.dumps(val)

        if isinstance(val, str):
            val_str = val.strip()
            if val_str.startswith(("{", "[")) and val_str.endswith(("}", "]")):
                try:
                    json.loads(val_str)
                    return True, val
                except json.JSONDecodeError:
                    pass
        return False, val

    def __navigate_path(self, json_data: Any, road: List[str]) -> tuple[Any, bool]:
        current_val = json_data
        for r in road:
            if isinstance(current_val, dict):
                if r in current_val:
                    current_val = current_val[r]
                else:
                    return None, False
            elif isinstance(current_val, list) and r.isdigit():
                idx = int(r)
                if 0 <= idx < len(current_val):
                    current_val = current_val[idx]
                else:
                    return None, False
            else:
                return None, False
        return current_val, True

    def __compare_operator(self, key: str, compare: str, val: Any, is_json: bool, sp_compare: tuple):
        def __contains_and_or(v: list, connector: str):
            if not v:
                return ("1=1" if connector == "AND" else "1=0"), []
            conditions = []
            params = []
            for item in v:
                if self._flag is True and not isinstance(item, (dict, list)):
                    # simple val
                    conditions.append(f"EXISTS(SELECT 1 FROM json_each({key}) WHERE value = ?)")
                    params.append(item)
                else:
                    # other | complicated val
                    conditions.append(f"instr({key}, ?) > 0")
                    params.append(json.dumps(item))
            return f" {connector} ".join(conditions), params

        operators = {
            "gt": (f"{key} > ?", [val]),
            "lt": (f"{key} < ?", [val]),
            "gte": (f"{key} >= ?", [val]),
            "lte": (f"{key} <= ?", [val]),
            "ne": (f"{key} != ?", [val]),
            "like": (f"{key} LIKE ?", [f"%{val}%"]),
            "startswith": (f"{key} LIKE ?", [f"{val}%"]),
            "endswith": (f"{key} LIKE ?", [f"%{val}"]),
        }
        if compare in operators:
            if compare == "ne" and self._flag and is_json:
                return f"NOT (json({key}) = json(?))", [val]
            return operators[compare]

        elif compare in ("contains", "any_contains"):
            if is_json:
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
            # list
            if isinstance(val, list):
                if compare == "contains":
                    return __contains_and_or(val, "AND")
                else:
                    return __contains_and_or(val, "OR")

            # single
            elif self._flag is True and not isinstance(val, (dict, list)):
                # simple val
                return f"EXISTS(SELECT 1 FROM json_each({key}) WHERE value = ?)", [val]

            else:
                # other | complicated val
                return f"instr({key}, ?) > 0", [json.dumps(val)]

        elif compare in ("in", "not_in"):
            if is_json:
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
            placeholders = ", ".join(["?"] * len(val))
            op = "IN" if compare == "in" else "NOT IN"
            return f"{key} {op} ({placeholders})", val

        self._q_error(key, compare, val, sp_compare)

    def __compare_reducer(self, key: str, compare: str, road: list, val: Any):
        sp_compare = getattr(self._fields.get(key), "compare")
        compare = compare.lower()
        # 没路径, 正常拦截op
        # 有路径, 最终字段类型是不确定的, 查询结果不可控
        if not sp_compare or compare not in [c.lower() for c in sp_compare]:
            if road:
                self._q_error(f"{key}__{road}", compare, val, sp_compare)
            else:
                self._q_error(key, compare, val, sp_compare)

        is_json, val = self.__is_json(val)
        if not road:
            sql, params = self.__compare_operator(
                f"{self._tb}.{key}", compare, val, is_json, sp_compare
            )
            return sql, params
        else:
            if self._flag:
                path = self.__generate_road(road)
                sql, params = self.__compare_operator(
                    f"json_extract({self._tb}.{key}, '{path}')", compare, val, is_json, sp_compare
                )
                return sql, params

            if is_json:
                try:
                    val = json.loads(val)
                except:
                    pass
            pk_name = self._model_class.__primary_key__
            q_fork = self._query.fork()
            db_rows = q_fork.select()
            matching_pks = []
            for row_dict in db_rows:
                field_json_str = row_dict.get(key)
                if field_json_str is None:
                    continue
                if isinstance(field_json_str, str):
                    try:
                        current_data = json.loads(field_json_str)
                    except (json.JSONDecodeError, TypeError):
                        continue
                elif isinstance(field_json_str, (dict, list)):
                    current_data = field_json_str
                else:
                    continue

                target_val, path_found = self.__navigate_path(current_data, road)
                if path_found:
                    if self._python_compare(target_val, compare, val):
                        pk_value = row_dict.get(pk_name)
                        if pk_value is not None:
                            matching_pks.append(pk_value)

            if matching_pks:
                placeholders = ",".join(["?"] * len(matching_pks))
                return f"{self._tb}.{pk_name} IN ({placeholders})", matching_pks
            else:
                return "1=0", []

    def __equal_reducer(self, key: str, road: list, val: Any):
        is_json, val = self.__is_json(val)
        if not road:  # normal field
            if val is not None:
                if self._flag is True and is_json:
                    return f"json({self._tb}.{key}) = json(?)", [val]
                return f"{self._tb}.{key} = ?", [val]

            return f"{self._tb}.{key} IS NULL", []
        if self._flag is True:
            path = self.__generate_road(road)
            if val is not None:
                if is_json:
                    return f"json_extract({self._tb}.{key}, ?) = json(?)", [path, val]
                return f"json_extract({self._tb}.{key}, ?) = ?", [path, val]

            return f"json_extract({self._tb}.{key}, ?) IS NULL", [path]
        pk_name = self._model_class.__primary_key__
        q_fork = self._query.fork()
        db_rows = q_fork.select()
        matching_pks = []
        new_val = json.loads(val) if is_json else val
        for row in db_rows:
            field_value = row.get(key)
            if field_value is None:
                continue
            try:
                if isinstance(field_value, str):
                    try:
                        field_value = json.loads(field_value)
                    except (json.JSONDecodeError, TypeError):
                        continue
                elif isinstance(field_value, (dict, list)):
                    field_value = field_value
                else:
                    continue
                target, path_found = self.__navigate_path(field_value, road)
                if path_found and self._deep_equal(target, new_val):
                    pk_value = row.get(pk_name)
                    if pk_value is not None:
                        matching_pks.append(pk_value)
            except:
                continue

        if matching_pks:
            placeholders = ",".join(["?"] * len(matching_pks))
            return f"{self._tb}.{pk_name} IN ({placeholders})", matching_pks
        return "1=0", []

    def __parse_condition(self, condition: Dict[str, Any]):
        """
        解析 key, compare, road, val
        field 字段
        compare 运算符, None为=
        road 路径
        val 值
        """
        for k, v in condition.items():
            parts = k.split("__")
            field = parts[0]

            if not field or not self._fields.get(field):
                print("Filter: %s's fields is not found: '%s' it will be pass" % (self._model_class.__name__, k))
                raise HintException("%s's fields is not found: '%s'" % (self._model_class.__name__, k))

            compare = None
            roads = []
            for part in parts[1:]:
                if part in COMPARE:
                    compare = part
                    break
                roads.append(part)

            yield field, compare, roads, v

    def reducer_process(self, condition: Dict[str, Any]) -> Generator[tuple[str, list[Any] | Any], Any, None]:
        for key, compare, road, val in self.__parse_condition(condition):
            if self._serializes and key in self._serializes:
                val = self._serializes[key].serialized(value=val, forward=True)

            if not compare:
                sql, params = self.__equal_reducer(key=key, road=road, val=val)
            else:
                if val is None:
                    raise HintException("do not try to use 'None' value to compare.")
                sql, params = self.__compare_reducer(key=key, compare=compare, road=road, val=val)

            if sql:
                yield sql, params


class Q:
    """
    嵌套查询
    AND优先级大于OR, 括号改变优先级
    example: model.object.filter( Q(a=1) & (Q(b=2) | Q(c=3)) )
    """
    AND = "AND"
    OR = "OR"

    def __init__(self, *args, _connector=None, **kwargs):
        self.children: list = []
        self._connector = _connector or self.AND
        for arg in args:
            if isinstance(arg, Q) and arg._connector == self._connector:
                self.children.extend(arg.children)
            elif isinstance(arg, (Q, dict)):
                self.children.append(arg)
            else:
                raise HintException(f"unsupported operand type(s) for Q: '{type(arg)}'")
        if kwargs:
            self.children.append(kwargs)

    def __and__(self, other):
        if not isinstance(other, Q):
            raise HintException(f"unsupported operand type(s) for &: 'Q' and '{type(other)}'")
        return Q(self, other, _connector=Q.AND)

    def __or__(self, other):
        if not isinstance(other, Q):
            raise HintException(f"unsupported operand type(s) for |: 'Q' and '{type(other)}'")
        return Q(self, other, _connector=Q.OR)

    def resolve(self, operator, query):
        for child in self.children:
            if isinstance(child, dict):
                for s, p in operator.reducer_process(child):
                    if s:
                        query.where(s, p)
            elif isinstance(child, Q):
                if child._connector == self._connector:
                    child.resolve(operator, query)
                else:
                    with query.where_nest(logic=self._connector) as n:
                        child.resolve(operator, n)
            else:
                raise HintException(f"Invalid child type: {type(child)}")


class QuerySet(Generic[M]):
    """
    查询集
    """

    def __init__(self, model_class: M, query: Db.query):
        self._model_class: M = model_class
        self._tb = self._model_class.__table_name__
        self._query = query
        self._cache = None
        self._field_filter = None

    def __len__(self):
        return len(self.__execute())

    def __bool__(self):
        return bool(self.__len__())

    def __iter__(self) -> Generator[M, None, None]:
        yield from self.__execute()

    def __getitem__(self, index: Optional[int | slice]) -> Optional[M | List[M]]:
        """
        查询结果切片
        """
        if isinstance(index, int):
            if self._cache is not None:
                try:
                    return self._cache[index]
                except IndexError:
                    raise HintException("list index out of range")
            else:
                new_q = self._query.fork()
                new_q.limit(index + 1, index)
                temp = new_q.find()
                return self._model_class(
                    _field_filter=self._field_filter,
                    **self._model_class._serialized_data(temp, self._field_filter)
                ) if temp else None
        elif isinstance(index, slice):
            if self._cache is not None:
                try:
                    return self._cache[index.start:index.stop]
                except IndexError:
                    raise HintException("list index out of range")
            else:
                self.__execute()
                return self._cache[index.start:index.stop]
        else:
            return None

    def __add__(self, other: "QuerySet") -> Iterable:
        """
        合并两个querset
        :return: 生成器
        """
        if not isinstance(other, QuerySet):
            raise HintException(f"nou support: 'QuerySet' and '{type(other)}'")

        if self._model_class != other._model_class:
            raise HintException("not the same model class cant be merged")
        return chain(self.__execute() or [], other.__execute() or [])

    def __execute(self) -> Optional[List[M]]:
        if self._cache is None:
            try:
                if len(self._query._SqliteEasy__OPT_FIELD._Field__FIELDS) == 0:
                    self._query.field(f"`{self._tb}`.*")

                self._cache = [
                    self._model_class(
                        _field_filter=self._field_filter,
                        **self._model_class._serialized_data(i, self._field_filter)
                    ) for i in self._query.select()
                ]
            except Exception as e:
                print("db query error => %s" % str(e))
                raise HintException(e)
        return self._cache

    def filter(self, *args, **kwargs) -> "QuerySet[M]":
        """
        过滤
        :return: QuerySet
        """
        operator = Operator(model_class=self._model_class, query=self._query)
        # args
        for i in args:
            if isinstance(i, Q):
                i.resolve(operator, self._query)
            elif isinstance(i, dict):
                for s, p in operator.reducer_process(i):
                    if s:
                        self._query.where(s, p)
            else:
                raise HintException(f"Invalid filter argument: {type(i)}")
        # kwargs
        for s, p in operator.reducer_process(kwargs):
            if s:
                self._query.where(s, p)
        return self

    def limit(self, num: int) -> "QuerySet[M]":
        """
        限制
        :return: QuerySet
        """
        self._query.limit(num)
        return self

    def offset(self, num: int) -> "QuerySet[M]":
        """
        偏移量
        :return: QuerySet
        """
        self._query.skip(num)
        return self

    def distinct(self) -> "QuerySet[M]":
        """
        以指定字段去重
        """
        return self

    def order_by(self, *args) -> "QuerySet[M]":
        """
        排序
        :param args: "filed" ASC "-filed" DESC
        :return: QuerySet
        """
        reduce(
            lambda q, c: q.order(f"{self._tb}.{c[1:]}", "DESC") if c[:1] == "-"
            else q.order(f"{self._tb}.{c}"), args, self._query
        )
        return self

    def fields(self, *args) -> "QuerySet[M]":
        if not args:
            return self
        field_set = set(args)
        # make suer pk
        pk = self._model_class.__primary_key__
        if pk not in field_set:
            field_set.add(pk)
        field_set = [f for f in field_set if f in self._model_class.__fields__]
        self._field_filter = field_set  # model level
        self._query.field(*(f"{self._tb}.{f}" for f in field_set))  # db level
        return self

    def first(self) -> Optional[M]:
        """
        获取第一条数据
        :return: QuerySet
        """
        if self._cache is None:
            if len(self._query._SqliteEasy__OPT_FIELD._Field__FIELDS) == 0:
                self._query.field(f"'{self._tb}'.*")
            data = self._query.find()
            if not data:
                return None
            return self._model_class(
                _field_filter=self._field_filter,
                **self._model_class._serialized_data(data, self._field_filter)
            )
        else:
            return self._cache[0] if len(self._cache) != 0 else None

    def get_field(self, key_name: str) -> Optional[Any]:
        """
        获取第一条数据的指定字段的值
        :param key_name: 字段名
        :return: Any
        """
        # noinspection PyUnresolvedReferences
        f = self.first().as_dict()
        return f.get(key_name) if f else None

    def update(self, *args, **kwargs) -> int:
        """
        更新数据
        :return: int
        """
        self._cache = None
        if args and kwargs:
            raise HintException("args and kwargs can not be used at the same time")
        if args:
            if len(args) != 1:
                raise HintException("%s too many args" % (args,))
            elif not isinstance(args[0], dict):
                raise HintException("%s must be a dict" % (args[0],))
            target = args[0]
        elif kwargs:
            target = kwargs
        else:
            target = None
        if not target:
            return 0
        count = 0
        for i in self._model_class._serialized_data(self._query.select(), self._field_filter):
            self._model_class(**{**i, **target}).save()
            count += 1
        return count

    def delete(self) -> int:
        """
        删除数据
        :return: int
        """
        self._cache = None
        count = self._query.delete()
        return count

    def exists(self) -> bool:
        """
        存在数据
        :return: bool
        """
        return bool(self.__execute())

    def count(self) -> int:
        """
        获取数量
        :return: int
        """
        if self._cache is None:
            self.__execute()
        return len(self._cache) if self._cache else 0

    def as_list(self) -> list:
        """
        转列表
        :return: list
        """
        if self._cache is None:
            self.__execute()
        return [x.as_dict() for x in self._cache]


class aaObjects(Generic[M]):
    """
    管理器
    """
    __m_map__ = {}

    def __new__(cls, args):
        if hasattr(args, "__table_name__") and not cls.__m_map__.get(args.__table_name__):
            cls.__m_map__[args.__table_name__] = aaMigrate(args).run_migrate()
            return super(aaObjects, cls).__new__(cls)
        else:
            return super(aaObjects, cls).__new__(cls)

    def __init__(self, model: M):
        self._model = model
        self.__q = None

    @property
    def _query(self) -> Db.query:
        if not self.__q:
            q = Db(self._model.__db_name__).query()
            self.__q = q.table(self._model.__table_name__)
            return self.__q
        else:
            return self.__q

    def _insert(self, val_data) -> int:
        return self._query.insert(val_data)

    def insert(self, data: Dict[str, Any], raise_exp: bool = True) -> dict:
        """
        插入单条数据
        :data dict
        :raise_exp bool 抛字段类型检查异常
        :return 插入的数据
        """
        model_obj = self._model(**data)
        insert_res = self._insert(
            model_obj._validate(raise_exp=raise_exp)
        )
        if insert_res:
            return {
                self._model.__primary_key__: insert_res, **model_obj.as_dict()
            }
        else:
            if raise_exp:
                raise HintException(insert_res)
            else:
                return {}

    def insert_many(self, data: List[Dict[str, Any]], raise_exp: bool = True) -> int:
        """
        批量插入数据
        :data list
        :raise_exp bool 不抛异常则跳过异常继续插入
        :return: int 影响行数
        """
        for i in data:
            try:
                self._model(**i)._validate(raise_exp=raise_exp)
            except Exception as e:
                if raise_exp:
                    raise HintException(f"{e}, data: {i}")
                else:
                    data.remove(i)
                    continue
        return self._query.insert_all(data)

    def find_one(self, **kwargs) -> Optional[M]:
        """
        过滤查询一行数据
        :kwargs dict
        :return: QuerySet | None
        """
        # noinspection PyUnresolvedReferences
        return QuerySet(self._model, self._query).filter(**kwargs).first()

    def filter(self, *args, **kwargs) -> "QuerySet[M]":
        """
        过滤
        :kwargs dict
        :return: QuerySet
        """
        return QuerySet(self._model, self._query).filter(*args, **kwargs)

    def all(self) -> "QuerySet[M]":
        """
        所有数据
        return: QuerySet
        """
        return QuerySet(self._model, self._query)


class aaMigrate:
    """
    同步表字段
    """
    NULL_MAP = {False: "NOT NULL", True: "NULL"}

    def __init__(self, model: M):
        self.__model = model
        self.__table = self.__model.__table_name__
        self.__fields = self.__model.__fields__
        self.__client = Db(model.__db_name__)
        self.__query = None

    def run_migrate(self) -> bool | None:
        """
        迁移
        """
        if not self.__model:
            raise PanelError("Model is None")
        if not hasattr(self.__model, '__db_name__'):
            raise PanelError(f"{self.__model.__class__.__name__} need 'db_name'")
        if not hasattr(self.__model, '__table_name__'):
            raise PanelError(f"{self.__model.__class__.__name__} need 'table_name'")
        if not hasattr(self.__model, '__fields__'):
            raise PanelError(f"{self.__model.__class__.__name__} need 'fields'")

        try:
            self.__table_exists()
            self.__index_exists()
        except Exception as e:
            raise PanelError(e)
        finally:
            self.__query.close()
            self.__client.close()
        return True

    def __new_tb_transform_sql(self, tb_name: str) -> str:
        """
        转sql
        """
        field_sql = ""
        pk_flag = 0
        for key, val in self.__fields.items():
            if key == "index":
                raise PanelError("'%s' is a reserved word in SQL. do not use it" % key)
            if val.primary_key is False:
                field_sql += f"`{key}` {val.field_type} {self.NULL_MAP.get(val.null)} {val.default_val_sql}, "
            else:  # is primary_key
                pk_flag += 1
                if val.field_type != "INTEGER":
                    raise PanelError("'primary_key' only support IntegerField now")
                field_sql += f"'{key}' {val.field_type} PRIMARY KEY AUTOINCREMENT, "
        if not field_sql:
            return ""
        if pk_flag != 1:
            raise PanelError("primary_key not found, and must be only one")
        field_sql = field_sql.rstrip(", ")
        sql = f"""CREATE TABLE IF NOT EXISTS `{tb_name}` ({field_sql});"""
        return sql

    def __fields_exist(self, add_fields_map: dict = None, del_fields: set = None, set_db: set = None) -> None:
        """
        字段处理
        """
        if not del_fields:
            for k, v in add_fields_map.items():
                add_sql = (f"ALTER TABLE `{self.__table}` "
                           f"ADD COLUMN `{k}` {v.field_type} {v.default_val_sql} {self.NULL_MAP.get(v.null)};")
                self.__query.execute(add_sql)
        else:
            if set_db:
                temp_tb = f"table_{uuid.uuid4().hex}"
                new = self.__new_tb_transform_sql(temp_tb)
                if new:
                    try:
                        self.__query.autocommit(autocommit=False)
                        self.__query.execute("BEGIN;")
                        self.__query.execute(new)
                        # rename fields will be loss old data now
                        format_keys = ", ".join(
                            [f"`{k}`" for k in set_db if k not in del_fields]
                        )
                        copy_sql = (f"INSERT INTO `{temp_tb}` ({format_keys}) "
                                    f"SELECT {format_keys} FROM `{self.__table}`;")
                        self.__query.execute(copy_sql)
                        self.__query.execute(f"DROP TABLE IF EXISTS `{self.__table}`;")
                        self.__query.execute(f"ALTER TABLE `{temp_tb}` RENAME TO `{self.__table}`;")
                        self.__query.commit()
                    except Exception as e:
                        import traceback
                        print(traceback.format_exc())
                        self.__query.rollback()
                        raise e

    def __table_exists(self) -> None:
        """
        表迁移
        """
        self.__query = self.__client.query().table("sqlite_master")
        if self.__query.where("type=? AND name=?", ("table", self.__table)).count() != 1:
            sql = self.__new_tb_transform_sql(self.__table)
            if sql:
                self.__query.execute(sql)
        else:  # has table
            self.__query.table(self.__table)
            set_cur = set(self.__fields.keys())
            set_db = set(self.__query.get_columns())
            add_fields = set_cur - set_db
            del_fields = set_db - set_cur
            add_fields_map = {k: v for k, v in self.__fields.items() if k in add_fields}
            self.__fields_exist(add_fields_map, del_fields, set_db)

    def __trans_index_key(self, index_info: tuple | str) -> str:
        def __if_raise_error(item: str):
            if not self.__model.__fields__.get(item):
                raise PanelError(f"create index error, '{item}' is not in model's fields")

        col_sql = ""
        if isinstance(index_info, tuple):
            for item in index_info:
                __if_raise_error(item)
                col_sql += f"`{item}`,"
        elif isinstance(index_info, str):
            __if_raise_error(index_info)
            col_sql = f"`{index_info}`"
        else:
            raise PanelError("model's index error, should be like ['key1', ('key2', 'key3')]")
        return col_sql.rstrip(",")

    def __index_exists(self) -> bool | None:
        """
        索引
        """
        try:
            self.__query.table(self.__table)
            cur = self.__query.query(f"PRAGMA index_list(`{self.__table}`);")
            current_index = [x.get("name") for x in cur] if cur else []
            sql_statements = []
            for index_info in self.__model.__index_keys__:
                """
                todo
                index_info 对应字段
                字段类型不为json: 普通索引
                如果为list:      分表, 索引, CURD触发, 存在性同步.
                如果为dict:      路径虚拟列索引
                复合索引 index_info tuple
                如果移除索引, 检查上述步骤
                """
                col_sql = self.__trans_index_key(index_info)
                cols = col_sql.split(",")
                cols = [col.strip("` ") for col in cols]
                index_name = f"idx_{self.__table}_{'_'.join(cols)}"

                if index_name not in current_index:
                    idx_sql = f"CREATE INDEX IF NOT EXISTS `{index_name}` ON `{self.__table}` ({col_sql}); "
                    sql_statements.append(idx_sql)
                else:
                    current_index.remove(index_name)

            for index in current_index:
                sql_statements.append(f"DROP INDEX IF EXISTS `{index}`;")

            if sql_statements:
                combined_sql = " ".join(sql_statements)
                self.__query.execute_script(combined_sql)

            return True
        except:
            pass


class aaManager:
    def __get__(self, instance, cls: M):
        if instance is None:
            try:
                return aaObjects(cls)
            except Exception:
                import traceback
                raise PanelError(traceback.format_exc())
        raise RuntimeError(
            f"object manager can't accessible from '{cls.__name__}' instances"
        )

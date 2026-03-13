# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# config app
# ------------------------------

import copy
import os
import threading

try:
    import ujson as json
except ImportError:
    import json

__all__ = [
    "DictConfig",
    "ListConfig",
]


class _Ctx:
    """轻量锁+加载"""
    __slots__ = ("_mgr", "_save")

    def __init__(self, mgr: "SimpleConfig", save: bool = False):
        self._mgr = mgr
        self._save = save

    def __enter__(self):
        mgr = self._mgr
        mgr._lock.acquire()
        try:
            if not mgr._loaded:
                mgr._do_load()
        except:
            mgr._lock.release()
            raise
        return mgr._cache

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._save and exc_type is None:
                self._mgr._save()
        finally:
            self._mgr._lock.release()


class SimpleConfig(object):
    """json"""
    __slots__ = ("_path", "_tmp_path", "_lock", "_cache", "_loaded", "_default")

    def __init__(self, path: str, default=None):
        """配置文件的绝对路径"""
        self._path: str = path
        self._default = default
        self._tmp_path: str = path + ".tmp"
        self._lock = threading.RLock()
        self._cache = None
        self._loaded: bool = False

        if default is not None and not os.path.exists(path):
            with self._lock:
                self._cache = copy.deepcopy(default)
                self._loaded = True
                self._save()

    def __bool__(self) -> bool:
        """判断当前数据是否非空"""
        with self._ctx() as c:
            return bool(c)

    def _ctx(self, save: bool = False) -> _Ctx:
        return _Ctx(self, save=save)

    def _do_load(self):
        """需持锁"""
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                self._loaded = True
                return
            except (ValueError, OSError):
                pass
        self._cache = copy.deepcopy(self._default) if self._default is not None else self._default_data()
        self._loaded = True

    def _save(self):
        """需持锁"""
        dirname = os.path.dirname(self._path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        try:
            with open(self._tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False)
                f.flush()
            os.replace(self._tmp_path, self._path)
        except OSError:
            self._loaded = False
            try:
                os.remove(self._tmp_path)
            except FileNotFoundError:
                pass
            raise

    def _default_data(self):
        raise NotImplementedError

    # ----------- public -----------

    def reload(self):
        """强制重新加载"""
        with self._lock:
            self._loaded = False
            self._do_load()

    def clear(self):
        """清空并持久化"""
        with self._ctx(save=True):
            self._cache = copy.deepcopy(self._default) if self._default is not None else self._default_data()

    def save(self):
        """手动持久化"""
        with self._ctx():
            if self._loaded:
                self._save()

    def atomic(self) -> _Ctx:
        """原子操作上下文, 事务"""
        return self._ctx(save=True)

    @property
    def path(self) -> str:
        return self._path

    def exists(self) -> bool:
        """配置文件是否存在于磁盘"""
        return os.path.exists(self._path)

    def delete_config(self):
        with self._lock:
            for p in (self._path, self._tmp_path):
                try:
                    os.remove(p)
                except FileNotFoundError:
                    pass
            self._cache = copy.deepcopy(self._default) if self._default is not None else self._default_data()
            self._loaded = True


# ---------------------------------------------------------------------------


class DictConfig(SimpleConfig):
    """
        cfg = DictConfig("/path/to/config.json", default={"a": 1})
        cfg.set("key", "value")
        cfg.get("key")            # "value"
        cfg.get("missing", 0)     # 0
        cfg["key"] = "new_value"
        del cfg["key"]
        cfg.update({"a": 1, "b": 2})      # 浅合并，整体覆盖同名 key
        cfg.merge({"a": {"x": 1}})        # 深合并，更新嵌套中若干字段而非整体覆盖
        cfg.keys() / cfg.values() / cfg.items()
        "key" in cfg
        len(cfg)
        cfg.pop("key", None)
        cfg.setdefault("key", default_val)
        cfg.as_dict()
    """

    def _default_data(self) -> dict:
        return {}

    def get(self, key: str, default=None):
        with self._ctx() as c:
            return c.get(key, default)

    def __getitem__(self, key: str):
        with self._ctx() as c:
            return c[key]

    def __contains__(self, key: str) -> bool:
        with self._ctx() as c:
            return key in c

    def __len__(self) -> int:
        with self._ctx() as c:
            return len(c)

    def __iter__(self):
        with self._ctx() as c:
            return iter(list(c.keys()))

    def keys(self):
        with self._ctx() as c:
            return list(c.keys())

    def values(self):
        with self._ctx() as c:
            return list(c.values())

    def items(self):
        with self._ctx() as c:
            return list(c.items())

    def as_dict(self) -> dict:
        with self._ctx() as c:
            return dict(c)

    def __repr__(self) -> str:
        with self._ctx() as c:
            return f"DictConfig({self._path!r}, {c!r})"

    def set(self, key: str, value) -> None:
        with self._ctx(save=True) as c:
            c[key] = value

    def __setitem__(self, key: str, value) -> None:
        with self._ctx(save=True) as c:
            c[key] = value

    def update(self, data: dict) -> None:
        if not data:
            return
        with self._ctx(save=True) as c:
            c.update(data)

    def merge(self, data: dict) -> None:
        """合并data到配置, 对嵌套dict递归合并, 非update覆盖"""
        if not data:
            return

        def _deep_merge(base: dict, patch: dict) -> None:
            for k, v in patch.items():
                if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                    _deep_merge(base[k], v)
                else:
                    base[k] = v

        with self._ctx(save=True) as c:
            _deep_merge(c, data)

    def setdefault(self, key: str, default=None):
        with self._ctx(save=True) as c:
            if key not in c:
                c[key] = default
            return c[key]

    def delete(self, key: str) -> None:
        with self._ctx(save=True) as c:
            if key in c:
                del c[key]

    def __delitem__(self, key: str) -> None:
        with self._ctx(save=True) as c:
            del c[key]

    def pop(self, key: str, *args):
        with self._ctx(save=True) as c:
            return c.pop(key, *args) if args else c.pop(key)


# ---------------------------------------------------------------------------


class ListConfig(SimpleConfig):
    """
        cfg = ListConfig("/path/to/list.json", default=[1,2,3])
        cfg.append("item") / cfg.insert(0, "x") / cfg.extend([...])
        cfg.get(0) / cfg[0] / cfg[0] = "v"
        cfg.remove("x") / cfg.pop(0) / del cfg[0]
        cfg.index("x") / cfg.count("x")
        "x" in cfg / len(cfg) / iter(cfg)
        cfg.sort() / cfg.reverse()
        cfg.unique()
        cfg.as_list()
    """

    def _default_data(self) -> list:
        return []

    def get(self, index: int, default=None):
        with self._ctx() as c:
            try:
                return c[index]
            except IndexError:
                return default

    def __getitem__(self, index):
        with self._ctx() as c:
            return c[index]

    def __contains__(self, item) -> bool:
        with self._ctx() as c:
            return item in c

    def __len__(self) -> int:
        with self._ctx() as c:
            return len(c)

    def __iter__(self):
        with self._ctx() as c:
            return iter(list(c))

    def count(self, item) -> int:
        with self._ctx() as c:
            return c.count(item)

    def index(self, item, *args) -> int:
        with self._ctx() as c:
            return c.index(item, *args)

    def as_list(self) -> list:
        with self._ctx() as c:
            return list(c)

    def __repr__(self) -> str:
        with self._ctx() as c:
            return f"ListConfig({self._path!r}, {c!r})"

    def set(self, index: int, value) -> None:
        with self._ctx(save=True) as c:
            c[index] = value

    def __setitem__(self, index, value) -> None:
        with self._ctx(save=True) as c:
            c[index] = value

    def __delitem__(self, index) -> None:
        with self._ctx(save=True) as c:
            del c[index]

    def append(self, item) -> None:
        with self._ctx(save=True) as c:
            c.append(item)

    def insert(self, index: int, item) -> None:
        with self._ctx(save=True) as c:
            c.insert(index, item)

    def extend(self, items) -> None:
        items = list(items)
        if not items:
            return
        with self._ctx(save=True) as c:
            c.extend(items)

    def remove(self, item) -> None:
        with self._ctx(save=True) as c:
            c.remove(item)

    def pop(self, index: int = -1):
        with self._ctx(save=True) as c:
            return c.pop(index)

    def sort(self, *, key=None, reverse: bool = False) -> None:
        with self._ctx(save=True) as c:
            c.sort(key=key, reverse=reverse)

    def reverse(self) -> None:
        with self._ctx(save=True) as c:
            c.reverse()

    def unique(self) -> None:
        """保序去重"""
        with self._ctx(save=True) as c:
            seen: set = set()
            result = []
            for item in c:
                try:
                    key = item
                    hash(key)
                except TypeError:
                    key = id(item)
                if key not in seen:
                    seen.add(key)
                    result.append(item)
            c[:] = result

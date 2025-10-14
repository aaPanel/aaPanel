# Hook __import__
import builtins
import os
import sys
import public
import public.PluginLoader as plugin_loader
import types
import traceback


if 'class_v2/' not in sys.path and 'class_v2' not in sys.path:
    sys.path.insert(0, 'class_v2/')


__basedir = public.get_panel_path()
__hooked = False
old__import__ = builtins.__import__


def hook_import():
    global __hooked, __basedir

    if __hooked:
        return

    def _aap__import__(name, globals = None, locals = None, fromlist = (), level = 0):
        try:
            return old__import__(name, globals, locals, fromlist, level)
        except SyntaxError:
            panel_path = __basedir

            # 处理相对导入
            if level > 0:
                if not globals or '__package__' not in globals:
                    raise ImportError("Attempted relative import with no known parent package")
                package = globals.get('__package__') or globals.get('__name__', '').rpartition('.')[0]
                if not package and level > 0:
                    raise ImportError("Attempted relative import with no known parent package")
                if level > 1:
                    parent_parts = package.split('.')
                    if len(parent_parts) < level - 1:
                        raise ImportError("Attempted relative import beyond top-level package")
                    package = '.'.join(parent_parts[:-level + 1])
                absolute_name = f"{package}.{name}" if name else package
            else:
                absolute_name = name

            # 如果模块已加载，直接返回
            if absolute_name in sys.modules:
                if fromlist is None or len(fromlist) == 0:
                    return sys.modules[absolute_name]

                is_loaded = True

                for name in fromlist:
                    if name == '*':
                        continue
                    if not hasattr(sys.modules[absolute_name], name):
                        is_loaded = False
                        break

                if is_loaded:
                    return sys.modules[absolute_name]


            module_path_part = absolute_name.replace('.', '/')
            is_package_import = bool(fromlist)

            for p in set(sys.path):
                base_path = os.path.join(panel_path, p)
                potential_file_path = os.path.realpath(os.path.join(base_path, module_path_part + '.py'))
                potential_dir_path = os.path.realpath(os.path.join(base_path, module_path_part))

                if os.path.isdir(potential_dir_path):
                    init_py = os.path.join(potential_dir_path, '__init__.py')

                    if os.path.exists(init_py) and os.path.getsize(init_py) > 10:
                        # 如果 __init__.py 存在并且不为空，作为常规包加载
                        top_module = plugin_loader.get_module(init_py)
                    else:
                        # 如果 __init__.py 不存在，创建一个空的模块对象来代表这个包
                        top_module = types.ModuleType(absolute_name)
                        top_module.__file__ = potential_dir_path
                        top_module.__path__ = [potential_dir_path]
                        top_module.__package__ = absolute_name
                        # 将创建的空模块放入 sys.modules 缓存
                        sys.modules[absolute_name] = top_module

                    if is_package_import:
                        for sub_module_name in fromlist:
                            if sub_module_name == '*':
                                continue
                            sub_module_path = os.path.join(potential_dir_path, sub_module_name + '.py')
                            if os.path.exists(sub_module_path):
                                try:
                                    sub_module = plugin_loader.get_module(sub_module_path)
                                    setattr(top_module, sub_module_name, sub_module)
                                except:
                                    traceback.print_exc()
                                    pass
                    return top_module

                elif os.path.exists(potential_file_path):
                    m = plugin_loader.get_module(potential_file_path)

                    # 规范化子模块对象属性
                    parts = absolute_name.split('.')
                    m.__name__ = absolute_name
                    m.__file__ = potential_file_path
                    m.__package__ = '.'.join(parts[:-1]) if len(parts) > 1 else ''

                    # 注册完整模块名到 sys.modules
                    sys.modules[absolute_name] = m

                    # 确保父包链存在并把子模块设置为父包属性（父包的 __path__ 指向模块文件所在目录）
                    for i in range(1, len(parts)):
                        parent_name = '.'.join(parts[:i])
                        child_name = parts[i]
                        if parent_name not in sys.modules:
                            parent = types.ModuleType(parent_name)
                            parent.__package__ = parent_name
                            # 将父包的 __path__ 指向包含子模块的目录（保守设置）
                            parent.__path__ = [os.path.dirname(potential_file_path)]
                            sys.modules[parent_name] = parent
                        else:
                            parent = sys.modules[parent_name]

                        # 设置父包对下级模块的属性引用（使用已经注册的模块对象）
                        child_full = '.'.join(parts[:i + 1])
                        child_mod = sys.modules.get(child_full)
                        if child_mod is not None:
                            setattr(parent, child_name, child_mod)

                    # 如果导入没有指定 fromlist（即通常的 `import a.b.c`），返回顶级包对象以匹配 CPython 行为
                    is_package_import = bool(fromlist)
                    if not is_package_import:
                        top_name = parts[0]
                        return sys.modules.get(top_name, m)

                    # 有 fromlist 时返回子模块对象
                    return m

            raise

    builtins.__import__ = _aap__import__

    __hooked = True


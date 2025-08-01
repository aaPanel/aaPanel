# Hook __import__
import builtins
import os
import sys
import public
import public.PluginLoader as plugin_loader
import types


if 'class_v2/' not in sys.path and 'class_v2' not in sys.path:
    sys.path.insert(0, 'class_v2/')


__hooked = False
old__import__ = builtins.__import__


def hook_import():
    global __hooked

    if __hooked:
        return

    def _aap__import__(name, globals = None, locals = None, fromlist = (), level = 0):
        try:
            return old__import__(name, globals, locals, fromlist, level)
        except SyntaxError:
            panel_path = public.get_panel_path()

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
                return sys.modules[absolute_name]

            module_path_part = absolute_name.replace('.', '/')
            is_package_import = bool(fromlist)

            for p in set(sys.path):
                base_path = os.path.join(panel_path, p)
                potential_file_path = os.path.join(base_path, module_path_part + '.py')
                potential_dir_path = os.path.join(base_path, module_path_part)

                top_module = None

                if os.path.isdir(potential_dir_path):
                    init_py = os.path.join(potential_dir_path, '__init__.py')

                    if os.path.exists(init_py):
                        # 如果 __init__.py 存在，作为常规包加载
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
                                except Exception:
                                    public.print_error()
                                    pass
                    return top_module

                elif os.path.exists(potential_file_path):
                    return plugin_loader.get_module(potential_file_path)

            raise

    builtins.__import__ = _aap__import__

    __hooked = True

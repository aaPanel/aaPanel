# Hook __import__
import builtins
import os
import sys
import public
import public.PluginLoader as plugin_loader


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
            # Handle both regular imports and relative imports
            if level > 0 and globals is not None:
                # This is a relative import
                package = globals.get('__package__')
                if package is None:
                    package = globals.get('__name__', '').rpartition('.')[0]

                # Calculate the absolute module path based on the relative path
                if not package and level > 0:
                    raise ImportError("Attempted relative import with no known parent package")

                if level > 1:
                    parent_parts = package.split('.')
                    if len(parent_parts) < level - 1:
                        raise ImportError("Attempted relative import beyond top-level package")
                    package = '.'.join(parent_parts[:-level+1])

                absolute_name = f"{package}.{name}" if name else package

                # Try to load the module with the calculated absolute path
                panel_path = public.get_panel_path()
                pyfile = '{}.py'.format(absolute_name.strip().replace('.', '/'))

                realpath = ''
                cond = False

                for p in set(sys.path):
                    realpath = os.path.join(panel_path, p, pyfile)
                    cond = os.path.exists(realpath)

                    if cond:
                        break

                if not cond:
                    realpath = os.path.join(panel_path, pyfile)
                    cond = os.path.exists(realpath)

                if cond:
                    try:
                        m = plugin_loader.get_module(realpath)

                        if fromlist is None or len(fromlist) == 0:
                            return m

                        for prop_name in fromlist:
                            prop = getattr(m, prop_name)

                            if globals is not None:
                                globals[prop_name] = prop

                            if locals is not None:
                                locals[prop_name] = prop

                        return m
                    except Exception:
                        raise
            # Regular absolute import handling
            elif level == 0 and str(name).strip() != '':
                panel_path = public.get_panel_path()
                pyfile = '{}.py'.format(str(name).strip().replace('.', '/'))

                realpath = ''
                cond = False

                for p in set(sys.path):
                    realpath = os.path.join(panel_path, p, pyfile)
                    cond = os.path.exists(realpath)

                    if cond:
                        break

                if not cond:
                    realpath = os.path.join(panel_path, pyfile)
                    cond = os.path.exists(realpath)

                if cond:
                    try:
                        m = plugin_loader.get_module(realpath)

                        if fromlist is None or len(fromlist) == 0:
                            return m

                        for prop_name in fromlist:
                            prop = getattr(m, prop_name)

                            if globals is not None:
                                globals[prop_name] = prop

                            if locals is not None:
                                locals[prop_name] = prop

                        return m
                    except Exception:
                        raise

            raise

    builtins.__import__ = _aap__import__

    __hooked = True

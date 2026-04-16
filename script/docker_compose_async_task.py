#!/www/server/panel/pyenv/bin/python
# coding: utf-8

import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")

import public
from btdockerModelV2 import composeModel


def _parse_task_id(argv):
    for i, arg in enumerate(argv):
        if arg == "--task-id" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--task-id="):
            return arg.split("=", 1)[1]
    return ""


def main():
    task_id = _parse_task_id(sys.argv)
    if not task_id:
        return

    composeModel.main().run_create_task(task_id)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        public.print_log(public.get_error_info())

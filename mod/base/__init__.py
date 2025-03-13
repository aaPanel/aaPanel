import time
from typing import Dict, List, Tuple, Union

from .process import RealProcess, Process
from .process import RealUser, User
from .process import RealServer, Server


def json_response(
        status: bool,
        msg: str = None,
        data: Union[Dict, List, Tuple, bool, str, int, float] = None,
        code: int = 0,
        args: Union[List[str], Tuple[str]] = None,
):
    if isinstance(msg, str) and args is not None:
        for i in range(len(args)):
            rep = '{' + str(i + 1) + '}'
            msg = msg.replace(rep, args[i])
    stn = 0 if status else -1
    if msg is None:
        msg = data

    # return {
    #     "status": status,
    #     "msg": msg,
    #     "data": data,
    #     "code": code,
    #     "timestamp": int(time.time())
    # }

    return {
        "status": stn,
        "timestamp": int(time.time()),
        "message": msg
    }

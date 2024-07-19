# 异常类
# @author Zhj<2024/06/27>

# 提示类异常 会正常响应
class HintException(Exception):
    pass


# 无授权异常
class NoAuthorizationException(HintException):
    pass

# coding: utf-8
from .fields import *
from .manager import Q, QueryProperty
from .model import aaModel

# from .file_model import *

__version__ = "1.1.3"

__all__ = [
              "__version__",
              # "DictFileModel",
              # "ListFileModel",
              "QueryProperty",
              "aaModel",
              "Q",
          ] + fields.__all__

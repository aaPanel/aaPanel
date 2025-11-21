# coding: utf-8
from .fields import *
from .manager import Q
from .model import aaModel

__version__ = "1.2.0"

__all__ = [
              "__version__",
              # "DictFileModel",
              # "ListFileModel",
              "aaModel",
              "Q",
          ] + fields.__all__

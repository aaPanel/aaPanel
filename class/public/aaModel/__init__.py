# coding: utf-8

from .fields import *
from .manager import Q, QueryProperty
from .model import aaModel

__version__ = "1.1.1"

__all__ = [
              "aaModel", "Q", "QueryProperty",
          ] + fields.__all__

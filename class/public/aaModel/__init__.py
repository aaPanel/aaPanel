# coding: utf-8

from .fields import *
from .model import aaModel
from .manager import Q
__version__ = "1.1.0"

__all__ = [
              "aaModel", "Q"
          ] + fields.__all__

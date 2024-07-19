# coding: utf-8
import os, sys, time, json

panelPath = '/www/server/panel'
os.chdir(panelPath)
if not panelPath + "/class/" in sys.path:
    sys.path.insert(0, panelPath + "/class/")
if not panelPath + "/class_v2/" in sys.path:
    sys.path.insert(0, panelPath + "/class_v2/")
import public, re


class monitorBase:

    def __init__(self):
        pass

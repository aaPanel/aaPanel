#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# sqlite模型
#------------------------------
import os,sys,re,json,shutil,psutil,time
from databaseModel.base import databaseBase
import public


class main(databaseBase):

    def get_list(self,args):

        return []
#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
from os import environ
from BTPanel import app,sys

if __name__ == '__main__':
    f = open('data/port.pl')
    PORT = int(f.read())
    HOST = '0.0.0.0'
    f.close()
    app.run(host=HOST,port=PORT)

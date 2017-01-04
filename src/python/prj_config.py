#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Ian'
__create_date__ = '2015/1/7'

import sys
import os


# 获取self_site 的绝对路径
CUR_DIR_NAME = os.path.dirname(__file__)

PATH_SELF_SITE = os.path.normpath(os.path.abspath(os.path.join(CUR_DIR_NAME, 'rs')))
print PATH_SELF_SITE


packageList = ['pillow==2.7.0']

# 执行安装包的命令
for pkg in packageList:
    cur_dir = PATH_SELF_SITE
    command = 'pip install -v --install-option=" ' \
              '--install-base=%s ' \
              '--install-purelib=%s/lib ' \
              '--install-scripts=%s/Scripts ' \
              '--install-lib=%s/self-site" %s' % (cur_dir, cur_dir, cur_dir, cur_dir, pkg)
    print command
    os.system(command)

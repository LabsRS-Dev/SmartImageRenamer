#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Ian'
__create_date__ = '2015/1/8'

## opensubtitles
LANGUAGE_MATRIX = []
f = open('MainMenu.strings', 'r')
f.readline()
for l in f:
    str = l.decode('utf-8').strip()

    if not str.startswith("/*"):
        LANGUAGE_MATRIX.append(str)
f.close()


fw = open('MainMenu_opt.strings', 'wb')
for str in LANGUAGE_MATRIX:
    if str != '':
        fw.write(str.encode("utf-8"))
    else:
        fw.write("\n")
fw.close()
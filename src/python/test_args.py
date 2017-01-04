#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Ian'
__create_date__ = '2015/1/17'
import argparse
import itertools
import os
import re
import sys


def get_cmd_args():
    """Get, process and return command line arguments to the script
    """
    help_description = '''
Smart Image Renamer

Rename your photos in bulk using information stored in EXIF.
'''

    help_epilog = '''
Format string for the file name is defined by a mix of custom text and following tags enclosed in {}:
  YYYY        Year
  MM          Month
  DD          Day
  hh          Hours
  mm          Minutes
  ss          Seconds
  Seq         Sequence number
  Artist      Artist
  Make        Camera Make
  Model       Camera Model
  Folder      Parent folder of the image file

Examples:
  Format String:          {YYYY}-{MM}-{DD}-{Folder}-{Seq}
  File Name:              2014-05-09-Wedding_Shoot-001.JPEG
                          2014-05-09-Wedding_Shoot-002.JPEG

  Format String:          {YYYY}{DD}{MM}_{Model}_Beach_Shoot_{Seq}
  File Name:              20140429_PENTAX K-x_Beach_Shoot_001.JPEG
                          20140429_PENTAX K-x_Beach_Shoot_002.JPEG
    '''

    parser = argparse.ArgumentParser(description=help_description,
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=help_epilog)
    parser.add_argument('-f', dest='format', required=True, type=str,
                        help='Format of the new file name')
    parser.add_argument('-s', dest='sequence', type=int, default=1,
                        help='Starting sequence number (default: 1)')
    parser.add_argument('-r', dest='recursive', default=False,
                        action='store_true',
                        help='Recursive mode')
    parser.add_argument('-i', dest='hidden', default=False,
                        action='store_true', help='Include hidden files')
    parser.add_argument('-t', dest='test', default=False, action='store_true',
                        help='Test mode. Don\'t apply changes.')

    parser.add_argument('-o', dest='outDir', type=str, help='Output Dir')

    # parser.add_argument('-V', '--version', action='version',
    #                     version='%(prog)s {}'.format(__version__))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument('input', nargs='+',
                        help='Absolute path to file or directory')

    return parser.parse_args()


if __name__ == '__main__':
    print sys.argv
    args = get_cmd_args()
    print args


    #Test1: -f "{YYYY}{DD}{MM}_Beach_Shoot_{Seq}" -r -i   -s 1 ""
    #Test2: -f "{YYYY}{DD}{MM}_Beach_Shoot_{Seq}" --no-r --no-i   -s 1 ""
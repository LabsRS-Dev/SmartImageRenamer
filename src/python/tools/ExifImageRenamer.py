#! /usr/bin/python
# -*- coding: utf-8 -*-

# smart-image-renamer
#
# Author: Ronak Gandhi (ronak.gandhi@ronakg.com)
# Project Home Page: https://github.com/ronakg/smart-image-renamer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Smart Image Renamer main module"""

import argparse
import itertools
import os
import re

from PIL import Image
from PIL.ExifTags import TAGS

# from _version import __version__


class NotAnImageFile(Exception):
    """This file is not an Image"""
    pass


class InvalidExifData(Exception):
    """Could not find any EXIF or corrupted EXIF"""
    pass


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

    parser.add_argument('-w', dest='overwrite', default=False, action='store_true',
                        help='Overwrite existing files')

    parser.add_argument('-d', dest='deleteSource', default=False, action='store_true',
                        help='Delete source files')

    # parser.add_argument('-V', '--version', action='version',
    # version='%(prog)s {}'.format(__version__))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true")
    group.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument('input', nargs='+',
                        help='Absolute path to file or directory')

    return parser.parse_args()


def get_exif_data(img_file):
    """Read EXIF data from the image.

    img_file: Absolute path to the image file

    Returns: A dictionary containing EXIF data of the file

    Raises: NotAnImageFile if file is not an image
            InvalidExifData if EXIF can't be processed
    """
    try:
        img = Image.open(img_file)
    except (OSError, IOError):
        raise NotAnImageFile

    try:
        # Use TAGS module to make EXIF data human readable
        exif_data = {
            TAGS[k]: v
            for k, v in img._getexif().items()
            if k in TAGS
        }
    except AttributeError:
        raise InvalidExifData

    # Add image format to EXIF
    exif_data['format'] = img.format
    return exif_data


def exifImageRenameCLI():
    skipped_files = []
    processed_filesMap = []
    args = get_cmd_args()
    print args

    input_paths = [os.path.abspath(input) for input in args.input]
    input_format = args.format
    verbose = args.verbose
    quiet = args.quiet
    sequence_start = args.sequence
    test_mode = args.test
    recursive = args.recursive
    include_hidden = args.hidden
    overwrite_mode = args.overwrite
    delete_source_mode = args.deleteSource

    for input_path in input_paths:
        unicodePath = None
        if not isinstance(input_path, unicode):
            unicodePath = unicode(input_path, 'utf-8')
        else:
            unicodePath = input_path

        for root, dirs, files in os.walk(unicodePath):
            # Skip hidden directories unless specified by user 
            if not include_hidden and os.path.basename(root).startswith('.'):
                continue

            # Initialize sequence counter
            # Use no of files to determine padding for sequence numbers
            seq = itertools.count(start=sequence_start)
            seq_width = len(str(len(files)))

            print('Processing folder: {}'.format(root))
            for f in sorted(files):
                # Skip hidden files unless specified by user 
                if not include_hidden and f.startswith('.'):
                    continue

                old_file_path = os.path.join(root, f)
                old_file_path = os.path.normpath(os.path.abspath(old_file_path))
                try:
                    # Get EXIF data from the image
                    exif_data = get_exif_data(old_file_path)
                except NotAnImageFile:
                    print old_file_path, 'not a image file'
                    continue
                except InvalidExifData:
                    skipped_files.append((old_file_path, 'No EXIF data found'))
                    continue

                # Find out the original timestamp or digitized timestamp from the EXIF
                img_timestamp = (exif_data.get('DateTimeOriginal') or
                                 exif_data.get('DateTimeDigitized'))

                if not img_timestamp:
                    skipped_files.append((old_file_path,
                                          'No timestamp found in image EXIF'))
                    continue

                # Extract year, month, day, hours, minutes, seconds from timestamp
                img_timestamp = \
                    re.search(r'(?P<YYYY>\d\d\d?\d?):(?P<MM>\d\d?):(?P<DD>\d\d?) '
                              '(?P<hh>\d\d?):(?P<mm>\d\d?):(?P<ss>\d\d?)',
                              img_timestamp.strip())

                if not img_timestamp:
                    skipped_files.append((old_file_path,
                                          'Timestamp not in correct format'))
                    continue

                outFolder = (args.outDir is not None) and args.outDir or root
                # Generate data to be replaced in user provided format
                new_image_data = {'Artist': exif_data.get('Artist', ''),
                                  'Make': exif_data.get('Make', ''),
                                  'Model': exif_data.get('Model', ''),
                                  # 'Folder': os.path.basename(root),
                                  'Folder': os.path.basename(outFolder),
                                  'Seq': '{0:0{1}d}'.format(next(seq), seq_width),
                                  'ext': exif_data.get('format', '')
                }
                new_image_data.update(img_timestamp.groupdict())

                # Generate new file name according to user provided format
                new_file_path = (input_format + '.{ext}').format(**new_image_data)
                new_file_path_complete = os.path.join(outFolder, new_file_path)

                # check new file is exist?
                b_new_file_exist = os.path.isfile(new_file_path_complete) \
                                   and os.path.exists(new_file_path_complete)

                suffix_seq = 0  # suffix process
                if not overwrite_mode:
                    while b_new_file_exist:
                        suffix = '_u' + str(suffix_seq)
                        new_file_path = (input_format + suffix + '.{ext}').format(**new_image_data)
                        new_file_path_complete = os.path.join(outFolder, new_file_path)
                        b_new_file_exist = os.path.isfile(new_file_path_complete) \
                                           and os.path.exists(new_file_path_complete)
                        suffix_seq += 1
                else:
                    # 检查格式化内容是个定值
                    org_input_format = input_format
                    img_data_format = input_format.format(**new_image_data)
                    if org_input_format == img_data_format:
                        while b_new_file_exist:
                            suffix = '_s' + str(suffix_seq)
                            new_file_path = (input_format + suffix + '.{ext}').format(**new_image_data)
                            new_file_path_complete = os.path.join(outFolder, new_file_path)
                            b_new_file_exist = os.path.isfile(new_file_path_complete) \
                                               and os.path.exists(new_file_path_complete)
                            suffix_seq += 1

                # 格式化路径
                new_file_path_complete = os.path.normpath(os.path.abspath(new_file_path_complete))
                old_in_dir = os.path.normpath(os.path.abspath(os.path.dirname(old_file_path)))
                new_in_dir = os.path.normpath(os.path.abspath(os.path.dirname(new_file_path_complete)))
                # Don't rename files if we are running in test mode
                if not test_mode:
                    try:
                        f_old = f_new = None
                        # (1)原路径和目标路径相同
                        if old_file_path == new_file_path_complete:
                            pass # 什么都不要做
                        # (2)原路径和目标路径在同一个目录，但全路径不同
                        elif old_in_dir == new_in_dir:
                            if b_new_file_exist and not overwrite_mode: # 目标文件已经存在，但不让覆盖，只能跳过
                                raise OSError('disable overwrite exist files. exist file ('
                                              + new_file_path_complete + ')')
                            elif b_new_file_exist and overwrite_mode: # 目标文件存在，让其覆盖
                                os.remove(new_file_path_complete)

                            if delete_source_mode:
                                os.rename(old_file_path, new_file_path_complete)
                            else:
                                f_old = open(old_file_path, "rb")
                                f_new = open(new_file_path_complete, "wb")
                                f_new.write(f_old.read())
                                f_old.close()
                                f_new.close()
                        # (3)原路径和目标路径在不同目录
                        else:
                            if b_new_file_exist and not overwrite_mode: # 目标文件已经存在，但不让覆盖，只能跳过
                                raise OSError('disable overwrite exist files. exist file ('
                                              + new_file_path_complete + ')')
                            elif b_new_file_exist and overwrite_mode: # 目标文件存在，让其覆盖
                                os.remove(new_file_path_complete)

                            f_old = open(old_file_path, "rb")
                            f_new = open(new_file_path_complete, "wb")
                            f_new.write(f_old.read())
                            f_old.close()
                            f_new.close()
                            # 不在同一目录，而且要求删除原文件
                            if delete_source_mode:
                                try:
                                    os.remove(old_file_path)
                                except OSError as e:
                                    print e.__str__()

                    except OSError as e:
                        skipped_files.append((old_file_path,
                                              'Failed to rename file. ' + e.__str__()))
                        continue
                    finally:
                        if f_old != None:
                            f_old.close()
                        if f_new != None:
                            f_new.close()

                # Add old,new file to processed_filesMap
                processed_filesMap.append({'old': old_file_path, 'new': new_file_path_complete})

                if verbose:
                    print('{0} --> {1}'.format(old_file_path,
                                               new_file_path_complete))
                elif not quiet:
                    print('{0} --> {1}'.format(f, new_file_path))

            # Folder processed
            print('')

            # Break if recursive flag is not present
            if not recursive:
                break

    # Print skipped files
    if skipped_files and not quiet:
        print('\nSkipped Files:\n\t' + '\n\t'.join([file + ' (' + error + ')'
                                                    for file, error in
                                                    skipped_files]))

    CLIResult = {
        'processed': processed_filesMap,
        'skipped': [{'file': file, 'error': error} for file, error in skipped_files]
    }

    return CLIResult


if __name__ == '__main__':
    exifImageRenameCLI()
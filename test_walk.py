#!/usr/bin/env python2
### Copyright (C) 2013 Peter Williams <pwil3058@gmail.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; version 2 of the License only.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import os
import argparse
import hashlib
import errno
import fnmatch
import re
import stat

parser = argparse.ArgumentParser(description="Test os.walk().")
parser.add_argument("dir_path", metavar="dir", type=str, nargs="?", help="the path of the directory to be walked")
parser.add_argument("--xfile", action="append", required=False, help="exclude files matching this pattern")
parser.add_argument("--xdir", action="append", required=False, help="exclude directories matching this pattern")

args = parser.parse_args()

EXCLUDE_FILE_CRES = [re.compile(fnmatch.translate(glob)) for glob in args.xfile] if args.xfile else []

def is_excluded_file(file_path):
    for cre in EXCLUDE_FILE_CRES:
        if cre.match(file_path):
            return True
    return False

EXCLUDE_DIR_CRES = [re.compile(fnmatch.translate(glob)) for glob in args.xdir] if args.xdir else []

def is_excluded_dir(dir_path):
    for cre in EXCLUDE_DIR_CRES:
        if cre.match(dir_path):
            return True
    return False

# The file has gone away
FORGIVEABLE_ERRNOS = frozenset((errno.ENOENT, errno.ENXIO))

file_data = {}

for dir_path, subdir_paths, file_names in os.walk(args.dir_path, followlinks=False):
    print "DIR:", dir_path
    if is_excluded_dir(dir_path):
        print "SKIP:", dir_path
        continue
    for file_name in file_names:
        if is_excluded_file(file_name):
            print "SKIP:", file_name
            continue
        file_path = os.path.join(dir_path, file_name)
        if is_excluded_file(file_path):
            print "SKIP:", file_path
            continue
        try:
            file_stats = os.lstat(file_path)
        except OSError as edata:
            # race condition
            if edata.errno in FORGIVEABLE_ERRNOS:
                continue # it's gone away so we skip it
            raise edata # something we can't handle so throw the towel in
        # for the moment we'll skip symbolic links
        if not stat.S_ISREG(file_stats.st_mode):
            continue
        try:
            content = open(file_path, "r").read()
        except OSError as edata:
            # race condition
            if edata.errno in FORGIVEABLE_ERRNOS:
                continue  # it's gone away so we skip it
            raise edata # something we can't handle so throw the towel in
        hex_digest = hashlib.sha1(content).hexdigest()
        file_data[file_path] = (file_stats.st_uid, file_stats.st_gid, file_stats.st_mode, hex_digest)
    excluded_subdir_paths = [subdir_path for subdir_path in subdir_paths if is_excluded_dir(subdir_path)]
    # NB: this is an in place reduction in the list of subdirectories
    for esdp in excluded_subdir_paths:
        print "SKIP SUBDIR:", esdp
        subdir_paths.remove(esdp)

print "DONE"

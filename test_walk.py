#!/usr/bin/env python2
### Copyright (C) 2015 Peter Williams <pwil3058@gmail.com>
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
import sys
import time

from epygibus_pkg import snapshot

parser = argparse.ArgumentParser(description="Test os.walk().")
parser.add_argument("dir_path", metavar="dir", type=str, nargs="?", default=".", help="the path of the directory to be walked")
parser.add_argument("--xfile", action="append", required=False, help="exclude files matching this pattern")
parser.add_argument("--xdir", action="append", required=False, help="exclude directories matching this pattern")
parser.add_argument("--snapshot", required=False, help="name of file in which to save the snapshot data")
parser.add_argument("--prior", required=False, help="name of file containing prior snapshot data")

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

new_snapshot = snapshot.Snapshot()

start_load = time.clock()
prior_snapshot = snapshot.read_snapshot(args.prior) if args.prior else snapshot.Snapshot()
stop_load = time.clock()
print "LOAD:", stop_load - start_load

content_count = 0
files_count = 0

start = time.clock()

for dir_path, subdir_paths, file_names in os.walk(args.dir_path, followlinks=False):
    if is_excluded_dir(dir_path):
        continue
    file_data = new_snapshot.add_subdir(dir_path, os.lstat(dir_path)).files
    prior_dir = prior_snapshot.find_dir(dir_path)
    prior_file_data = {} if prior_dir is None else prior_dir.files
    for file_name in file_names:
        if is_excluded_file(file_name):
            continue
        file_path = os.path.join(dir_path, file_name)
        if is_excluded_file(file_path):
            continue
        try:
            file_stats = os.lstat(file_path)
        except OSError as edata:
            # race condition
            if edata.errno in FORGIVEABLE_ERRNOS:
                continue # it's gone away so we skip it
            raise edata # something we can't handle so throw the towel in
        if stat.S_ISREG(file_stats.st_mode):
            prior_file = prior_file_data.get(file_name, None) if prior_file_data else None
            if prior_file and (prior_file[0].st_size == file_stats.st_size) and (prior_file[0].st_mtime == file_stats.st_mtime):
                hex_digest = prior_file[1]
            else:
                try:
                    content = open(file_path, "r").read()
                except OSError as edata:
                    # race condition
                    if edata.errno in FORGIVEABLE_ERRNOS:
                        continue  # it's gone away so we skip it
                    raise edata # something we can't handle so throw the towel in
                hex_digest = hashlib.sha1(content).hexdigest()
            content_count += file_stats.st_size
            file_data[file_name] = (file_stats, hex_digest)
        elif stat.S_ISLNK(file_stats.st_mode):
            try:
                target_file_path = os.readlink(file_path)
            except OSError as edata:
                # race condition
                if edata.errno in FORGIVEABLE_ERRNOS:
                    continue  # it's gone away so we skip it
                raise edata # something we can't handle so throw the towel in
            if not os.path.exists(target_file_path):
                # no sense storing broken links as they will cause problems at restore
                sys.stderr.write("{0} -> {1} symbolic link is broken.  Skipping.\n".format(file_path, target_file_path))
                continue
            file_data[file_name] = (file_stats, target_file_path)
        else:
            continue
        files_count += 1
    excluded_subdir_paths = [subdir_path for subdir_path in subdir_paths if is_excluded_dir(subdir_path)]
    # NB: this is an in place reduction in the list of subdirectories
    for esdp in excluded_subdir_paths:
        subdir_paths.remove(esdp)

stop = time.clock()

etime = stop - start

print "DONE", files_count, content_count, etime, content_count / etime / 1000000, files_count / etime

start_dump = time.clock()
snapshot.write_snapshot(args.snapshot, new_snapshot)
stop_dump = time.clock()
print "DUMP:", stop_dump - start_dump

for d in new_snapshot.find_dir(args.dir_path).iterate_subdirs():
    print d

for f in new_snapshot.find_dir(args.dir_path).iterate_files():
    print f

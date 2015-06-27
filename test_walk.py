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
import sys
import time

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

class Directory(object):
    def __init__(self, dir_stats=None):
        self.dir_stats = dir_stats
        self.subdirs = {}
        self.files = {}
    def __str__(self):
        string = "\n".join([str(self.dir_stats), str(self.files)])
        for name, subdir in self.subdirs.items():
            string += "\n{0}:{1}\n".format(name, str(subdir))
        return string
    def _add_subdir(self, path_parts, dir_stats=None):
        name = path_parts[0]
        if len(path_parts) == 1:
            self.subdirs[name] = Directory(dir_stats)
            return self.subdirs[name]
        else:
            if name not in self.subdirs:
                self.subdirs[name] = Directory()
            return self.subdirs[name]._add_subdir(path_parts[1:], dir_stats)
    def add_subdir(self, dir_path, dir_stats=None):
        return self._add_subdir(dir_path.strip(os.sep).split(os.sep), dir_stats)
    def _find_dir(self, dirpath_parts):
        if not dirpath_parts:
            return self
        elif dirpath_parts[0] in self.subdirs:
            return self.subdirs[dirpath_parts[0]]._find_dir(dirpath_parts[1:])
        else:
            return None
    def find_dir(self, dirpath):
        if not dirpath:
            return self
        return self._find_dir(dirpath.strip(os.sep).split(os.sep))

base_dir = Directory()

if args.prior:
    import cPickle
    fobj = open(args.prior, 'rb')
    try:
        prior_snapshot = cPickle.load(fobj)
    except Exception:
        # Just in case higher level code catches and handles
        prior_snapshot = None
        raise
    finally:
        fobj.close()
else:
    prior_snapshot = Directory()

content_count = 0

start = time.clock()

for dir_path, subdir_paths, file_names in os.walk(args.dir_path, followlinks=False):
    if is_excluded_dir(dir_path):
        continue
    file_data = base_dir.add_subdir(dir_path, os.lstat(dir_path)).files
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
    excluded_subdir_paths = [subdir_path for subdir_path in subdir_paths if is_excluded_dir(subdir_path)]
    # NB: this is an in place reduction in the list of subdirectories
    for esdp in excluded_subdir_paths:
        subdir_paths.remove(esdp)

stop = time.clock()

etime = stop - start

print "DONE", len(file_data), content_count, etime, content_count / etime / 1000000, len(file_data) / etime

if args.snapshot:
    import cPickle
    fobj = open(args.snapshot, 'wb', stat.S_IRUSR|stat.S_IRGRP)
    try:
        cPickle.dump(base_dir, fobj)
    finally:
        fobj.close()

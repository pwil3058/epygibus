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

start_load = time.clock()
prior_snapshot = snapshot.read_snapshot(args.prior) if args.prior else snapshot.Snapshot()
stop_load = time.clock()
print "LOAD:", stop_load - start_load

content_count = 0
files_count = 0

start = time.clock()

ss_gen = snapshot.SnapshotGenerator(snapshot.DummyBlobMgr())

ss_gen.include_dir(args.dir_path)

stop = time.clock()

etime = stop - start

print "DONE", files_count, content_count, etime, content_count / etime / 1000000, files_count / etime

start_dump = time.clock()
snapshot.write_snapshot(args.snapshot, ss_gen.snapshot)
stop_dump = time.clock()
print "DUMP:", stop_dump - start_dump

for d in ss_gen.snapshot.find_dir(args.dir_path).iterate_subdirs():
    print d

for f in ss_gen.snapshot.find_dir(args.dir_path).iterate_files():
    print f

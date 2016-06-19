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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import os
import time
import argparse
import mmap
import io

parser = argparse.ArgumentParser(description="Test various options for getting file sha1 digest for a directory.")
parser.add_argument("dir_path", metavar="directory", type=str, action="store", help="the path of the direcory whose files' digests are to be calculated")

args = parser.parse_args()

def hex_digest_mmap(file_path):
    f = io.open(file_path, "rb")
    try:
        m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        hd = hashlib.sha1(m).hexdigest()
        m.close()
        f.close()
    except ValueError:
        hd = hashlib.sha1(b"").hexdigest()
    return hd

def hex_digest_read(file_path):
    return hashlib.sha1(io.open(file_path, "rb").read()).hexdigest()

def hex_digest_read_chunks(file_path):
    h = hashlib.sha1()
    with io.open(file_path, "rb") as f:
        for x in iter(lambda: f.read(10000000), b""):
            h.update(x)
    return h.hexdigest()

def walk_the_tree(directory_path, functn, iterations=5):
    count = 0
    total_bytes = 0
    abs_dir_path = os.path.abspath(os.path.expanduser(directory_path))
    start = os.times()[4]
    for dir_path, subdir_names, file_names in os.walk(abs_dir_path, followlinks=False):
        for file_name in file_names:
            file_path = os.path.join(dir_path, file_name)
            if not os.path.isfile(file_path): continue
            total_bytes += os.path.getsize(file_path)
            count += 1
            for i in range(iterations):
                functn(file_path)
    return (os.times()[4] - start, count, total_bytes)

for name in ["hex_digest_read", "hex_digest_mmap", "hex_digest_read_chunks"]:
    print (name, walk_the_tree(args.dir_path, eval(name)))

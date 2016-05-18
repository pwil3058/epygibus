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

import hashlib
import os
import time
import argparse
import mmap

parser = argparse.ArgumentParser(description="Test various options for getting file sha1 digest.")
parser.add_argument("file_path", metavar="file", type=str, action="store", help="the path of the file whose digest is to be calculated")

args = parser.parse_args()

file_sz = os.path.getsize(args.file_path)

def hex_digest_mmap(file_path):
    f = open(file_path, "rb")
    m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    hd = hashlib.sha1(m).hexdigest()
    m.close()
    f.close()
    return hd

def hex_digest_read(file_path):
    return hashlib.sha1(open(file_path, "rb").read()).hexdigest()

def hex_digest_read_chunks(file_path):
    h = hashlib.sha1()
    with open(file_path, "rb") as f:
        for x in iter(lambda: f.read(10000000), ""):
            h.update(x)
    return h.hexdigest()

iterations = 5

total = 0
total_sq = 0

for i in range(iterations):
    start_time = time.clock()
    hd = hex_digest_read_chunks(args.file_path)
    duration = time.clock() - start_time
    total += duration
    total += duration * duration

print file_sz, total / iterations, hd

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
import shutil

parser = argparse.ArgumentParser(description="Test various options for copying files")
parser.add_argument("fm_file_path", metavar="from", type=str, action="store", help="the path of the file to be copied")
parser.add_argument("to_file_path", metavar="to", type=str, action="store", help="where the file is to be copied")

args = parser.parse_args()

file_sz = os.path.getsize(args.fm_file_path)

iterations = 5

total = 0
total_sq = 0

def copy_read_write(fm_path, to_path):
    open(to_path, "wb").write(open(fm_path, "rb").read())

def copy_copyfileobj(fm_path, to_path, bufsize):
    tof = open(to_path, "wb")
    fmf = open(fm_path, "rb")
    shutil.copyfileobj(fmf, tof, bufsize)

for i in range(iterations):
    start_time = time.clock()
    #copy_read_write(args.fm_file_path, args.to_file_path)
    #shutil.copy(args.fm_file_path, args.to_file_path)
    copy_copyfileobj(args.fm_file_path, args.to_file_path)
    duration = time.clock() - start_time
    total += duration
    total += duration * duration

print file_sz, total / iterations

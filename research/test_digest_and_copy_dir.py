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
import io
import shutil

parser = argparse.ArgumentParser(description="Test various options for getting file sha1 digest for a directory and copying all files.")
parser.add_argument("dir_path", metavar="directory", type=str, action="store", help="the path of the direcory whose files are to be processed")

args = parser.parse_args()

TGT_FILE = "TMPFILE"
EMPTY_FILE_HASH = hashlib.sha1(b"").hexdigest()

def hex_digest_mmap(fobj):
    try:
        m = mmap.mmap(fobj.fileno(), 0, access=mmap.ACCESS_READ)
        hd = hashlib.sha1(m).hexdigest()
        m.close()
    except ValueError:
        hd = EMPTY_FILE_HASH
    return hd

def hex_digest_read(fobj):
    hd = hashlib.sha1(fobj.read()).hexdigest()
    fobj.seek(0)
    return hd

def hex_digest_read_chunks(fobj):
    h = hashlib.sha1()
    for x in iter(lambda: fobj.read(10000000), b""):
        h.update(x)
    fobj.seek(0)
    return h.hexdigest()

def hex_digest_and_copyfileobj(file_path, hd_fun):
    # two levels of with to mic what repo code will need
    with io.open(file_path, "rb") as f_in:
        hd = hd_fun(f_in)
        with io.open(TGT_FILE, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    return hd

def hex_digest_and_read_write(file_path, hd_fun):
    with io.open(file_path, "rb") as f_in:
        hd = hd_fun(f_in)
        with io.open(TGT_FILE, "wb") as f_out:
            f_out.write(f_in.read())
    return hd

def walk_the_tree(directory_path, functn_0, functn_1):
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
            functn_0(file_path, functn_1)
            assert os.path.getsize(file_path) == os.path.getsize(TGT_FILE)
    return (os.times()[4] - start, count, total_bytes)

for wname in ["hex_digest_and_copyfileobj", "hex_digest_and_read_write"]:
    for name in ["hex_digest_read", "hex_digest_mmap", "hex_digest_read_chunks"]:
        print (wname, ":", name, "->", walk_the_tree(args.dir_path, eval(wname), eval(name)))

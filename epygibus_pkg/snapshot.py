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
import collections
import stat

class FStatsMixin:
    @property
    def is_dir(self):
        return stat.S_ISDIR(self.fstats.st_mode)
    @property
    def is_link(self):
        return stat.S_ISLNK(self.fstats.st_mode)
    @property
    def is_reg_file(self):
        return stat.S_ISREG(self.fstats.st_mode)
    @property
    def mode(self):
        return self.fstats.st_mode
    @property
    def mtime(self):
        return self.fstats.st_mtime
    @property
    def nlink(self):
        return self.fstats.st_nlink
    @property
    def size(self):
        return self.fstats.st_size
    @property
    def uid(self):
        return self.fstats.st_uid
    @property
    def gid(self):
        return self.fstats.st_gid

class SDir(collections.namedtuple("SDir", ["path", "fstats", "subdirs", "files"]), FStatsMixin):
    pass

class SFile(collections.namedtuple("SFile", ["path", "fstats", "content"]), FStatsMixin):
    @property
    def link_tgt(self):
        return seld.content if stat.S_ISLNK(self.fstats.st_mode) else None
    @property
    def hex_digest(self):
        return seld.content if stat.S_ISREG(self.fstats.st_mode) else None

class Snapshot(object):
    def __init__(self, dir_stats=None):
        self.dir_stats = dir_stats
        self.subdirs = {}
        self.files = {}
    def _add_subdir(self, path_parts, dir_stats=None):
        name = path_parts[0]
        if len(path_parts) == 1:
            self.subdirs[name] = Snapshot(dir_stats)
            return self.subdirs[name]
        else:
            if name not in self.subdirs:
                self.subdirs[name] = Snapshot()
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
    def find_dir(self, dir_path):
        if not dir_path:
            return self
        return self._find_dir(dir_path.strip(os.sep).split(os.sep))
    def iterate_files(self, pre_path="", recurse=False):
        for file_name, data in self.files.items():
            yield SFile(os.path.join(pre_path, file_name), data[0], data[1])
        if recurse:
            for dir_name in self.subdirs:
                for sfile in self.subdirs[dir_name].iterate_files(os.path.join(pre_path, dir_name), recurse=recurse):
                    yield sfile
    def iterate_subdirs(self, pre_path="", recurse=False):
        for subdir_name, data in self.subdirs.items():
            yield SDir(os.path.join(pre_path, subdir_name), data.dir_stats, data.subdirs, data.files)
        if recurse:
            for dir_name in self.subdirs:
                for sfile in self.subdirs[dir_name].iterate_subdirs(os.path.join(pre_path, dir_name), recurse=recurse):
                    yield sfile

def read_snapshot(snapshot_file_path):
    import cPickle
    if snapshot_file_path.endswith(".gz"):
        import gzip
        fobj = gzip.open(snapshot_file_path, "rb")
    else:
        fobj = open(snapshot_file_path, "rb")
    return cPickle.load(fobj)

def write_snapshot(snapshot_file_path, snapshot, permissions=stat.S_IRUSR|stat.S_IRGRP):
    import cPickle
    if snapshot_file_path.endswith(".gz"):
        import gzip
        fobj = gzip.open(snapshot_file_path, "wb")
    else:
        fobj = open(snapshot_file_path, "wb")
    cPickle.dump(snapshot, fobj)
    os.chmod(snapshot_file_path, permissions)

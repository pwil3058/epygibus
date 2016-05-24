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
import cPickle
from contextlib import contextmanager
import errno
import gzip
import os

class BlobManager(object):
    REF_COUNTER_FILE_NAME = "ref_counter"
    LOCK_FILE_NAME = "lock"
    def __init__(self, base_dir_path):
        self._base_dir_path = base_dir_path
        self._ref_counter_path = os.path.join(self._base_dir_path, self.REF_COUNTER_FILE_NAME)
        self._lock_file_path = os.path.join(self._base_dir_path, self.LOCK_FILE_NAME)
    def store_contents(self, file_path):
        contents = open(file_path, "r").read()
        hex_digest = hashlib.sha1(contents).hexdigest()
        dir_name, file_name = hex_digest[:2], hex_digest[2:]
        dir_path = os.path.join(self._base_dir_path, dir_name)
        needs_write = True
        with self.blobs_locked(exclusive=True):
            ref_counter = cPickle.load(open(self._ref_counter_path, "rb"))
            if dir_name not in ref_counter:
                ref_counter[dir_name] = { file_name : 1 }
                os.mkdir(dir_path)
            elif file_name not in ref_counter[dir_name]:
                ref_counter[dir_name][file_name] = 1
            else:
                ref_counter[dir_name][file_name] += 1
                needs_write = False
            cPickle.dump(ref_counter, open(self._ref_counter_path, "wb"))
            # TODO: think about moving content writing out of lock context
            if needs_write:
                import stat
                file_path = os.path.join(dir_path, file_name)
                open(file_path, "w").write(contents)
                os.chmod(file_path, stat.S_IRUSR|stat.S_IRGRP)
        return hex_digest
    def release_contents(self, hex_digest):
        # NB: we leave the removal of unreferenced blobs to others
        dir_name, file_name = hex_digest[:2], hex_digest[2:]
        with self.blobs_locked(exclusive=True):
            ref_counter = cPickle.load(open(self._ref_counter_path, "rb"))
            ref_counter[dir_name][file_name] -= 1
            cPickle.dump(ref_counter, open(self._ref_counter_path, "wb"))
    def fetch_contents(self, hex_digest):
        file_path = os.path.join(self._base_dir_path, hex_digest[:2], hex_digest[2:])
        with self.blobs_locked(exclusive=False):
            try:
                contents = open(file_path, "r").read()
            except OSError as edata:
                if edata.errno != errno.ENOENT:
                    raise edata
                contents = gzip.open(file_path + ".gz", "r").read()
        return contents
    def open_read_only(self, hex_digest):
        file_path = os.path.join(self._base_dir_path, hex_digest[:2], hex_digest[2:])
        with self.blobs_locked(exclusive=False):
            try:
                ofile = open(file_path, "r")
            except OSError as edata:
                if edata.errno != errno.ENOENT:
                    raise edata
                ofile = gzip.open(file_path + ".gz", "r")
        return ofile
    @contextmanager
    def blobs_locked(self, exclusive=False):
        import fcntl
        fobj = os.open(self._lock_file_path, os.O_RDWR if exclusive else os.O_RDONLY)
        fcntl.lockf(fobj, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.lockf(fobj, fcntl.LOCK_UN)
            os.close(fobj)

def open_repo(repo_name):
    from . import config
    return BlobManager(config.read_repo_spec(repo_name).base_dir_path)

def initialize_repo(base_dir_path):
    ref_counter_path = os.path.join(base_dir_path, BlobManager.REF_COUNTER_FILE_NAME)
    cPickle.dump(dict(), open(ref_counter_path, "wb"))
    lock_file_path = os.path.join(base_dir_path, BlobManager.LOCK_FILE_NAME)
    open(lock_file_path, "wb").write("blob_lock")

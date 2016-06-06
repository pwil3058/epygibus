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
import collections

_REF_COUNTER_FILE_NAME = "ref_counter"
_LOCK_FILE_NAME = "lock"
_ref_counter_path = lambda base_dir_path: os.path.join(base_dir_path, _REF_COUNTER_FILE_NAME)
_lock_file_path = lambda base_dir_path: os.path.join(base_dir_path, _LOCK_FILE_NAME)
_split_hex_digest = lambda hex_digest: (hex_digest[:2], hex_digest[2:])

BlobRepoData = collections.namedtuple("BlobRepoData", ["base_dir_path", "ref_counter_path", "lock_file_path"])

def get_blob_repo_data(repo_name):
    from . import config
    from . import excpns
    base_dir_path = config.read_repo_spec(repo_name).base_dir_path
    return BlobRepoData(base_dir_path, _ref_counter_path(base_dir_path), _lock_file_path(base_dir_path))

class _BlobRepo(collections.namedtuple("_BlobRepo", ["ref_counter", "base_dir_path", "writeable"])):
    def store_contents(self, file_path):
        assert self.writeable
        contents = open(file_path, "r").read()
        hex_digest = hashlib.sha1(contents).hexdigest()
        dir_name, file_name = _split_hex_digest(hex_digest)
        dir_path = os.path.join(self.base_dir_path, dir_name)
        needs_write = True
        if dir_name not in self.ref_counter:
            self.ref_counter[dir_name] = { file_name : 1 }
            os.mkdir(dir_path)
        elif file_name not in self.ref_counter[dir_name]:
            self.ref_counter[dir_name][file_name] = 1
        else:
            self.ref_counter[dir_name][file_name] += 1
            needs_write = False
        if needs_write:
            import stat
            file_path = os.path.join(dir_path, file_name)
            open(file_path, "w").write(contents)
            os.chmod(file_path, stat.S_IRUSR|stat.S_IRGRP)
        return (hex_digest, needs_write)
    def incr_ref_count(self, hex_digest):
        assert self.writeable
        dir_name, file_name = _split_hex_digest(hex_digest)
        self.ref_counter[dir_name][file_name] += 1
    def release_content(self, hex_digest):
        assert self.writeable
        dir_name, file_name = _split_hex_digest(hex_digest)
        self.ref_counter[dir_name][file_name] -= 1
    def release_contents(self, hex_digests):
        assert self.writeable
        for hex_digest in hex_digests:
            dir_name, file_name = _split_hex_digest(hex_digest)
            self.ref_counter[dir_name][file_name] -= 1
    def iterate_hex_digests(self):
        for dir_name, dir_data in self.ref_counter.items():
            for file_name, count in dir_data.items():
                try:
                    size = os.path.getsize(os.path.join(self.base_dir_path, dir_name, file_name))
                except EnvironmentError:
                    size = None
                yield (dir_name + file_name, count, size)
    def prune_unreferenced_blobs(self):
        assert self.writeable
        blob_count = 0
        total_bytes = 0
        for dir_name, dir_data in self.ref_counter.items():
            for file_name, count in dir_data.items():
                if count: continue
                blob_count += 1
                file_path = os.path.join(self.base_dir_path, dir_name, file_name)
                total_bytes += os.path.getsize(file_path)
                try:
                    os.remove(file_path)
                except EnvironmentError as edata:
                    if edata.errno != errno.ENOENT:
                        raise edata
                    os.remove(file_path + ".gz")
                del dir_data[file_name]
        return (blob_count, total_bytes) #if blob_count else None
    def open_blob_read_only(self, hex_digest):
        # NB since this doen't use ref count data it doesn't need locking
        file_path = os.path.join(self.base_dir_path, *_split_hex_digest(hex_digest))
        try:
            return open(file_path, "r")
        except EnvironmentError as edata:
            if edata.errno != errno.ENOENT:
                raise edata
            return gzip.open(file_path + ".gz", "r")
    def copy_contents_to(self, hex_digest, target_file_path):
        import shutil
        file_path = os.path.join(self.base_dir_path, *_split_hex_digest(hex_digest))
        try:
            shutil.copy(file_path, target_file_path)
        except EnvironmentError as edata:
            if edata.errno != errno.ENOENT:
                raise edata
            open(target_file_path, "w").write(gzip.open(file_path + ".gz", "r").read())

@contextmanager
def open_blob_repo(blob_repo_data, writeable=False):
    import fcntl
    fobj = os.open(blob_repo_data.lock_file_path, os.O_RDWR if writeable else os.O_RDONLY)
    fcntl.lockf(fobj, fcntl.LOCK_EX if writeable else fcntl.LOCK_SH)
    ref_counter = cPickle.load(open(blob_repo_data.ref_counter_path, "rb"))
    try:
        yield _BlobRepo(ref_counter, blob_repo_data.base_dir_path, writeable)
    finally:
        if writeable:
            cPickle.dump(ref_counter, open(blob_repo_data.ref_counter_path, "wb"), cPickle.HIGHEST_PROTOCOL)
        fcntl.lockf(fobj, fcntl.LOCK_UN)
        os.close(fobj)

def initialize_repo(repo_spec):
    try:
        os.makedirs(repo_spec.base_dir_path)
    except EnvironmentError as edata:
        if edata.errno == errno.EEXIST:
            raise excpns.BlobRepositoryLocationExists(repo_spec.name)
        elif edata.errno == errno.EPERM:
            raise excpns.BlobRepositoryLocationNoPerm(repo_spec.name)
        else:
            raise edata
    ref_counter_path = _ref_counter_path(repo_spec.base_dir_path)
    cPickle.dump(dict(), open(ref_counter_path, "wb"))
    lock_file_path = _lock_file_path(repo_spec.base_dir_path)
    open(lock_file_path, "wb").write("blob_lock")

def create_new_repo(repo_name, location_dir_path):
    from . import config
    from . import excpns
    repo_spec = config.write_repo_spec(repo_name, location_dir_path)
    try:
        initialize_repo(repo_spec)
    except (EnvironmentError, excpns.Error) as edata:
        config.delete_repo_spec(repo_spec.name)
        raise edata

def compress_repository(repo_name):
    from . import utils
    brd = get_blob_repo_data(repo_name)
    for entry_name in os.listdir(brd.base_dir_path):
        entry_path = os.path.join(brd.base_dir_path, entry_name)
        if os.path.isdir(entry_path):
            with open_blob_repo(brd, True): # don't hog the lock
                for file_name in os.listdir(entry_path):
                    if not file_name.endswith(".gz"):
                        utils.compress_file(os.path.join(entry_path, file_name))

def uncompress_repository(repo_name):
    from . import utils
    brd = get_blob_repo_data(repo_name)
    for entry_name in os.listdir(brd.base_dir_path):
        entry_path = os.path.join(brd.base_dir_path, entry_name)
        if os.path.isdir(entry_path):
            with open_blob_repo(brd, True): # don't hog the lock
                for file_name in os.listdir(entry_path):
                    if file_name.endswith(".gz"):
                        utils.uncompress_file(os.path.join(entry_path, file_name))

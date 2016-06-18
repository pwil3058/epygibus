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
from contextlib import contextmanager
import errno
import gzip
import os
import collections
import io

try:
    import cPickle as pickle
except ImportError:
    import pickle

_REF_COUNTER_FILE_NAME = "ref_counter"
_LOCK_FILE_NAME = "lock"
_ref_counter_path = lambda base_dir_path: os.path.join(base_dir_path, _REF_COUNTER_FILE_NAME)
_lock_file_path = lambda base_dir_path: os.path.join(base_dir_path, _LOCK_FILE_NAME)
_ld1 = 1
_ld2 = _ld1 + 2
_split_content_token = lambda content_token: (content_token[:_ld1], content_token[_ld1:_ld2], content_token[_ld2:])

BlobRepoData = collections.namedtuple("BlobRepoData", ["base_dir_path", "ref_counter_path", "lock_file_path", "compressed"])

class CIS(collections.namedtuple("CIS", ["stored_size", "ref_count"])):
    @property
    def stored_size_per_ref(self):
        if self.ref_count > 1:
            return float(self.stored_size) / self.ref_count
        else:
            return self.stored_size
    def __add__(self, other):
        return CIS(*[self[i] + other[i] for i in range(len(self))])

def get_repo_mgmt_key(repo_name):
    from . import config
    from . import excpns
    repo_spec = config.read_repo_spec(repo_name)
    return BlobRepoData(repo_spec.base_dir_path, _ref_counter_path(repo_spec.base_dir_path), _lock_file_path(repo_spec.base_dir_path), repo_spec.compressed)

class _BlobRepo(collections.namedtuple("_BlobRepo", ["ref_counter", "base_dir_path", "writeable", "compressed"])):
    def store_contents(self, file_path):
        assert self.writeable
        contents = io.open(file_path, "rb").read()
        content_token = hashlib.sha1(contents).hexdigest()
        dir_name, subdir_name, file_name = _split_content_token(content_token)
        dir_path = os.path.join(self.base_dir_path, dir_name)
        subdir_path = os.path.join(dir_path, subdir_name)
        needs_write = True
        if dir_name not in self.ref_counter:
            self.ref_counter[dir_name] = { subdir_name : { file_name : 1 }}
            os.mkdir(dir_path)
            os.mkdir(subdir_path)
        elif subdir_name not in self.ref_counter[dir_name]:
            self.ref_counter[dir_name][subdir_name] = { file_name : 1 }
            os.mkdir(subdir_path)
        elif file_name not in self.ref_counter[dir_name][subdir_name]:
            self.ref_counter[dir_name][subdir_name][file_name] = 1
        else:
            self.ref_counter[dir_name][subdir_name][file_name] += 1
            needs_write = False
        if needs_write:
            import stat
            file_path = os.path.join(subdir_path, file_name)
            if self.compressed:
                file_path += ".gz"
                with gzip.open(file_path, "wb") as fobj:
                    fobj.write(contents)
            else:
                with io.open(file_path, "wb") as fobj:
                    fobj.write(contents)
            os.chmod(file_path, stat.S_IRUSR|stat.S_IRGRP)
        # NB returning content storage stats here has been tried and
        # rejected due to time penalties (3 orders of magnitude) on
        # slow file systems such as cifs mounted network devices
        return content_token
    def _content_stored_size(self, *token_parts):
        file_path = os.path.join(self.base_dir_path, *token_parts)
        if self.compressed: # try compressed first
            try: # but allow for the case that they've been uncompressed
                return os.path.getsize(file_path + ".gz")
            except EnvironmentError:
                return os.path.getsize(file_path)
        else: # try uncompressed first
            try: # but allow for the case that they've been compressed
                return os.path.getsize(file_path)
            except EnvironmentError:
                return os.path.getsize(file_path + ".gz")
    def get_content_storage_stats(self, content_token):
        dir_name, subdir_name, file_name = _split_content_token(content_token)
        return CIS(self._content_stored_size(dir_name, subdir_name, file_name), self.ref_counter[dir_name][subdir_name][file_name])
    def release_content(self, content_token):
        assert self.writeable
        dir_name, subdir_name, file_name = _split_content_token(content_token)
        self.ref_counter[dir_name][subdir_name][file_name] -= 1
    def release_contents(self, content_tokens):
        assert self.writeable
        for content_token in content_tokens:
            dir_name, subdir_name, file_name = _split_content_token(content_token)
            self.ref_counter[dir_name][subdir_name][file_name] -= 1
    def iterate_content_tokens(self):
        for dir_name, dir_data in self.ref_counter.items():
            for subdir_name, subdir_data in dir_data.items():
                for file_name, count in subdir_data.items():
                    try:
                        size = os.path.getsize(os.path.join(self.base_dir_path, dir_name, subdir_name, file_name + ".gz"))
                    except EnvironmentError:
                        size = os.path.getsize(os.path.join(self.base_dir_path, dir_name, subdir_name, file_name))
                    yield (dir_name + subdir_name + file_name, count, size)
    def get_counts(self):
        num_refed = 0
        num_unrefed = 0
        ref_total = 0
        for dir_data in self.ref_counter.values():
            for subdir_data in dir_data.values():
                for count in subdir_data.values():
                    if count:
                        ref_total += count
                        num_refed += 1
                    else:
                        num_unrefed += 1
        return (num_refed, num_unrefed, ref_total)
    def prune_unreferenced_content(self, rm_empty_dirs=False, rm_empty_subdirs=True):
        assert self.writeable
        citem_count = 0
        total_bytes = 0
        for dir_name, dir_data in self.ref_counter.items():
            for subdir_name, subdir_data in dir_data.items():
                for file_name, count in subdir_data.items():
                    if count: continue
                    citem_count += 1
                    file_path = os.path.join(self.base_dir_path, dir_name, subdir_name, file_name)
                    try: # try the default first
                        total_bytes += os.path.getsize(file_path + ".gz")
                        os.remove(file_path + ".gz")
                    except EnvironmentError as edata:
                        if edata.errno != errno.ENOENT:
                            raise edata
                        total_bytes += os.path.getsize(file_path)
                        os.remove(file_path)
                    del subdir_data[file_name]
                if rm_empty_subdirs and len(dir_data[subdir_name]) == 0:
                    del dir_data[subdir_name]
                    os.rmdir(os.path.join(self.base_dir_path, dir_name, subdir_name))
            if rm_empty_dirs and len(self.ref_counter[dir_name]) == 0:
                del self.ref_counter[dir_name]
                os.rmdir(os.path.join(self.base_dir_path, dir_name))
        return (citem_count, total_bytes) #if citem_count else None
    def open_contents_read_only(self, content_token, binary=False):
        # NB since this doen't use ref count data it doesn't need locking
        file_path = os.path.join(self.base_dir_path, *_split_content_token(content_token))
        try:
            return gzip.open(file_path + ".gz", "rb" if binary else "r")
        except EnvironmentError as edata:
            if edata.errno != errno.ENOENT:
                raise edata
            return io.open(file_path, "rb" if binary else "r")
    def copy_contents_to(self, content_token, target_file_path):
        import shutil
        file_path = os.path.join(self.base_dir_path, *_split_content_token(content_token))
        try:
            shutil.copy(file_path, target_file_path)
        except EnvironmentError as edata:
            if edata.errno != errno.ENOENT:
                raise edata
            with gzip.open(file_path + ".gz", "rb") as f_in, io.open(target_file_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

@contextmanager
def open_repo_mgr(repo_mgmt_key, writeable=False):
    import fcntl
    fobj = os.open(repo_mgmt_key.lock_file_path, os.O_RDWR if writeable else os.O_RDONLY)
    fcntl.lockf(fobj, fcntl.LOCK_EX if writeable else fcntl.LOCK_SH)
    ref_counter = pickle.load(io.open(repo_mgmt_key.ref_counter_path, "rb"))
    try:
        yield _BlobRepo(ref_counter, repo_mgmt_key.base_dir_path, writeable, compressed=repo_mgmt_key.compressed)
    finally:
        if writeable:
            pickle.dump(ref_counter, io.open(repo_mgmt_key.ref_counter_path, "wb"), pickle.HIGHEST_PROTOCOL)
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
    pickle.dump(dict(), io.open(ref_counter_path, "wb"), pickle.HIGHEST_PROTOCOL)
    lock_file_path = _lock_file_path(repo_spec.base_dir_path)
    io.open(lock_file_path, "wb").write(b"content_repo_lock")

def create_new_repo(repo_name, location_dir_path, compressed):
    from . import config
    from . import excpns
    repo_spec = config.write_repo_spec(repo_name, location_dir_path, compressed)
    try:
        initialize_repo(repo_spec)
    except (EnvironmentError, excpns.Error) as edata:
        config.delete_repo_spec(repo_spec.name)
        raise edata

def compress_repository(repo_name):
    from . import utils
    brd = get_repo_mgmt_key(repo_name)
    for entry_name in os.listdir(brd.base_dir_path):
        entry_path = os.path.join(brd.base_dir_path, entry_name)
        if not os.path.isdir(entry_path): continue
        with open_repo_mgr(brd, True): # don't hog the lock
            for subdir_name in os.listdir(entry_path):
                subdir_path = os.path.join(entry_path, subdir_name)
                if not os.path.isdir(subdir_path): continue
                for file_name in os.listdir(subdir_path):
                    if not file_name.endswith(".gz"):
                        utils.compress_file(os.path.join(subdir_path, file_name))

def uncompress_repository(repo_name):
    from . import utils
    brd = get_repo_mgmt_key(repo_name)
    for entry_name in os.listdir(brd.base_dir_path):
        entry_path = os.path.join(brd.base_dir_path, entry_name)
        if not os.path.isdir(entry_path): continue
        with open_repo_mgr(brd, True): # don't hog the lock
            for subdir_name in os.listdir(entry_path):
                subdir_path = os.path.join(entry_path, subdir_name)
                if not os.path.isdir(subdir_path): continue
                for file_name in os.listdir(subdir_path):
                    if file_name.endswith(".gz"):
                        utils.uncompress_file(os.path.join(subdir_path, file_name))

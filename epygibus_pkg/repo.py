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
from contextlib import contextmanager
import errno
import gzip
import os
import collections
import io
import shutil

from .w2and3 import pickle, PICKLE_PROTOCOL

_REF_COUNTER_FILE_NAME = "ref_counter"
_LOCK_FILE_NAME = "lock"
_ref_counter_path = lambda base_dir_path: os.path.join(base_dir_path, _REF_COUNTER_FILE_NAME)
_lock_file_path = lambda base_dir_path: os.path.join(base_dir_path, _LOCK_FILE_NAME)
_ld1 = 1
_ld2 = _ld1 + 2
_split_content_token = lambda content_token: (content_token[:_ld1], content_token[_ld1:_ld2], content_token[_ld2:])

RepoMgmtKey = collections.namedtuple("RepoMgmtKey", ["base_dir_path", "ref_counter_path", "lock_file_path", "compressed"])

class CIS(collections.namedtuple("CIS", ["stored_size", "ref_count"])):
    @property
    def stored_size_per_ref(self):
        try:
            return float(self.stored_size) / self.ref_count
        except ZeroDivisionError:
            return self.stored_size
    def __add__(self, other):
        return CIS(*[self[i] + other[i] for i in range(len(self))])

def get_repo_mgmt_key(repo_name):
    from . import config
    from . import excpns
    repo_spec = config.read_repo_spec(repo_name)
    return RepoMgmtKey(repo_spec.base_dir_path, _ref_counter_path(repo_spec.base_dir_path), _lock_file_path(repo_spec.base_dir_path), repo_spec.compressed)

_REF_COUNT, _CONTENT_SIZE, _STORED_SIZE = range(3)

class _BlobRepo(collections.namedtuple("_BlobRepo", ["ref_counter", "base_dir_path", "writeable", "compressed"])):
    def store_contents(self, file_path):
        assert self.writeable
        with io.open(file_path, "rb") as f_in:
            content_token = hashlib.sha1(f_in.read()).hexdigest()
            dir_name, subdir_name, file_name = _split_content_token(content_token)
            dir_path = os.path.join(self.base_dir_path, dir_name)
            subdir_path = os.path.join(dir_path, subdir_name)
            needs_write = True
            if dir_name not in self.ref_counter:
                c_size = os.path.getsize(file_path)
                self.ref_counter[dir_name] = { subdir_name : { file_name : [1, c_size, c_size] }}
                os.mkdir(dir_path)
                os.mkdir(subdir_path)
            elif subdir_name not in self.ref_counter[dir_name]:
                c_size = os.path.getsize(file_path)
                self.ref_counter[dir_name][subdir_name] = { file_name : [1, c_size, c_size] }
                os.mkdir(subdir_path)
            elif file_name not in self.ref_counter[dir_name][subdir_name]:
                c_size = os.path.getsize(file_path)
                self.ref_counter[dir_name][subdir_name][file_name] = [1, c_size, c_size]
            else:
                self.ref_counter[dir_name][subdir_name][file_name][_REF_COUNT] += 1
                needs_write = False
            if needs_write:
                import stat
                f_in.seek(0)
                out_file_path = os.path.join(subdir_path, file_name)
                if self.compressed:
                    out_file_path += ".gz"
                    with gzip.open(out_file_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                else:
                    with io.open(out_file_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                self.ref_counter[dir_name][subdir_name][file_name][_STORED_SIZE] = os.path.getsize(out_file_path)
                os.chmod(out_file_path, stat.S_IRUSR|stat.S_IRGRP)
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
        return CIS(self._content_stored_size(dir_name, subdir_name, file_name), self.ref_counter[dir_name][subdir_name][file_name][_REF_COUNT])
    def release_content(self, content_token):
        assert self.writeable
        dir_name, subdir_name, file_name = _split_content_token(content_token)
        self.ref_counter[dir_name][subdir_name][file_name][_REF_COUNT] -= 1
    def release_contents(self, content_tokens):
        assert self.writeable
        for content_token in content_tokens:
            dir_name, subdir_name, file_name = _split_content_token(content_token)
            self.ref_counter[dir_name][subdir_name][file_name][_REF_COUNT] -= 1
    def iterate_content_tokens(self):
        for dir_name, dir_data in self.ref_counter.items():
            for subdir_name, subdir_data in dir_data.items():
                for file_name, data in subdir_data.items():
                    yield (dir_name + subdir_name + file_name, data[_REF_COUNT], data[_CONTENT_SIZE], data[_STORED_SIZE])
    def get_counts(self):
        num_refed = 0
        num_unrefed = 0
        ref_total = 0
        for dir_data in self.ref_counter.values():
            for subdir_data in dir_data.values():
                for count, c_size, s_size in subdir_data.values():
                    if count:
                        ref_total += count
                        num_refed += 1
                    else:
                        num_unrefed += 1
        return (num_refed, num_unrefed, ref_total)
    def prune_unreferenced_content(self, rm_empty_dirs=False, rm_empty_subdirs=True):
        assert self.writeable
        citem_count = 0
        total_content_bytes = 0
        total_stored_bytes = 0
        for dir_name, dir_data in self.ref_counter.items():
            for subdir_name, subdir_data in dir_data.items():
                for file_name, file_data in subdir_data.items():
                    count, content_size, stored_size = file_data
                    if count: continue
                    citem_count += 1
                    total_content_bytes += content_size
                    total_stored_bytes += stored_size
                    file_path = os.path.join(self.base_dir_path, dir_name, subdir_name, file_name)
                    try: # try the default first
                        os.remove(file_path + ".gz")
                    except EnvironmentError as edata:
                        if edata.errno != errno.ENOENT:
                            raise edata
                        os.remove(file_path)
                    del subdir_data[file_name]
                if rm_empty_subdirs and len(dir_data[subdir_name]) == 0:
                    del dir_data[subdir_name]
                    os.rmdir(os.path.join(self.base_dir_path, dir_name, subdir_name))
            if rm_empty_dirs and len(self.ref_counter[dir_name]) == 0:
                del self.ref_counter[dir_name]
                os.rmdir(os.path.join(self.base_dir_path, dir_name))
        return (citem_count, total_content_bytes, total_stored_bytes) #if citem_count else None
    def open_contents_read_only(self, content_token, binary=False):
        # NB since this doen't use ref count data it doesn't need locking
        file_path = os.path.join(self.base_dir_path, *_split_content_token(content_token))
        try:
            return gzip.open(file_path + ".gz", "rb" if binary else "r")
        except EnvironmentError as edata:
            if edata.errno != errno.ENOENT:
                raise edata
            return io.open(file_path, "rb" if binary else "r")
    def copy_contents_to(self, content_token, target_file_path, attributes):
        from . import excpns
        file_path = os.path.join(self.base_dir_path, *_split_content_token(content_token))
        try:
            with io.open(target_file_path, "wb") as f_out:
                try: # try compressed first as that is the default
                    with gzip.open(file_path + ".gz", "rb") as f_in:
                        shutil.copyfileobj(f_in, f_out)
                except EnvironmentError as edata:
                    if edata.errno != errno.ENOENT:
                        raise edata
                    with io.open(file_path, "rb") as f_in:
                        shutil.copyfileobj(f_in, f_out)
        except EnvironmentError as edata:
            raise excpns.CopyFileFailed(target_file_path, os.strerror(edata.errno))
        try:
            os.chmod(target_file_path, attributes.st_mode)
            os.utime(target_file_path, (attributes.st_atime, attributes.st_mtime))
            os.chown(target_file_path, attributes.st_uid, attributes.st_gid)
        except EnvironmentError as edata:
            raise excpns.SetAttributesFailed(target_file_path, os.strerror(edata.errno))

@contextmanager
def open_repo_mgr(repo_mgmt_key, writeable=False):
    import fcntl
    with io.open(repo_mgmt_key.lock_file_path, "wb" if writeable else "rb") as fobj:
        fcntl.lockf(fobj, fcntl.LOCK_EX if writeable else fcntl.LOCK_SH)
        with io.open(repo_mgmt_key.ref_counter_path, "rb") as ref_in:
            ref_counter = pickle.load(ref_in)
        try:
            yield _BlobRepo(ref_counter, repo_mgmt_key.base_dir_path, writeable, compressed=repo_mgmt_key.compressed)
        finally:
            if writeable:
                with io.open(repo_mgmt_key.ref_counter_path, "wb") as ref_out:
                    pickle.dump(ref_counter, ref_out, PICKLE_PROTOCOL)
            fcntl.lockf(fobj, fcntl.LOCK_UN)

def initialize_repo(repo_spec):
    from . import excpns
    try:
        os.makedirs(repo_spec.base_dir_path)
    except EnvironmentError as edata:
        if edata.errno == errno.EEXIST:
            raise excpns.BlobRepositoryLocationExists(repo_spec.name)
        elif edata.errno == errno.EPERM or edata.errno == errno.EACCES:
            raise excpns.BlobRepositoryLocationNoPerm(repo_spec.name)
        else:
            raise edata
    ref_counter_path = _ref_counter_path(repo_spec.base_dir_path)
    pickle.dump(dict(), io.open(ref_counter_path, "wb"), PICKLE_PROTOCOL)
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

def delete_repo(repo_name):
    from . import excpns
    from . import config
    rmk = get_repo_mgmt_key(repo_name)
    with open_repo_mgr(rmk, writeable=True) as repo_mgr:
        refed, _unrefed, _total = repo_mgr.get_counts()
        if refed:
            raise excpns.RepositoryInUse(repo_name, refed)
        config.delete_repo_spec(repo_name)
        repo_mgr.prune_unreferenced_content(rm_empty_dirs=True, rm_empty_subdirs=True)
    os.remove(rmk.ref_counter_path)
    os.remove(rmk.lock_file_path)
    os.rmdir(rmk.base_dir_path)

def compress_repository(repo_name):
    from . import utils
    saved_bytes = 0
    rmk = get_repo_mgmt_key(repo_name)
    for entry_name in os.listdir(rmk.base_dir_path):
        entry_path = os.path.join(rmk.base_dir_path, entry_name)
        if not os.path.isdir(entry_path): continue
        with open_repo_mgr(rmk, True) as repo_mgr: # don't hog the lock
            for subdir_name in os.listdir(entry_path):
                subdir_path = os.path.join(entry_path, subdir_name)
                if not os.path.isdir(subdir_path): continue
                for file_name in os.listdir(subdir_path):
                    if not file_name.endswith(".gz"):
                        file_data = repo_mgr.ref_counter[entry_name][subdir_name][file_name]
                        old_size = file_data[_STORED_SIZE]
                        file_data[_STORED_SIZE] = utils.compress_file(os.path.join(subdir_path, file_name))
                        saved_bytes += old_size - file_data[_STORED_SIZE]
    return saved_bytes

def uncompress_repository(repo_name):
    from . import utils
    extra_bytes = 0
    rmk = get_repo_mgmt_key(repo_name)
    for entry_name in os.listdir(rmk.base_dir_path):
        entry_path = os.path.join(rmk.base_dir_path, entry_name)
        if not os.path.isdir(entry_path): continue
        with open_repo_mgr(rmk, True) as repo_mgr: # don't hog the lock
            for subdir_name in os.listdir(entry_path):
                subdir_path = os.path.join(entry_path, subdir_name)
                if not os.path.isdir(subdir_path): continue
                for file_name in os.listdir(subdir_path):
                    if file_name.endswith(".gz"):
                        file_data = repo_mgr.ref_counter[entry_name][subdir_name][file_name[:-3]]
                        old_size = file_data[_STORED_SIZE]
                        file_data[_STORED_SIZE] = utils.uncompress_file(os.path.join(subdir_path, file_name))
                        extra_bytes += file_data[_STORED_SIZE] - old_size
    return extra_bytes

class BRSS(collections.namedtuple("BRSS", ["references", "referenced_items", "referenced_content_bytes", "referenced_stored_bytes", "unreferenced_items", "unreferenced_content_bytes", "unreferenced_stored_bytes"])):
    @property
    def total_items(self):
        return self.referenced_items + self.unreferenced_items
    @property
    def total_content_bytes(self):
        return self.referenced_content_bytes + self.unreferenced_content_bytes
    @property
    def total_stored_bytes(self):
        return self.referenced_stored_bytes + self.unreferenced_stored_bytes

def get_repo_storage_stats(repo_name):
    repo_mgmt_key = get_repo_mgmt_key(repo_name)
    total_references = 0
    total_referenced_items = 0
    total_referenced_content_bytes = 0
    total_referenced_stored_bytes = 0
    total_unreferenced_items = 0
    total_unreferenced_content_bytes = 0
    total_unreferenced_stored_bytes = 0
    with open_repo_mgr(repo_mgmt_key, True) as repo_mgr:
        for dir_name, dir_data in repo_mgr.ref_counter.items():
            for subdir_name, subdir_data in dir_data.items():
                for count, content_bytes, stored_bytes in subdir_data.values():
                    if count:
                        total_references += count
                        total_referenced_items += 1
                        total_referenced_content_bytes += content_bytes
                        total_referenced_stored_bytes += stored_bytes
                    else:
                        total_unreferenced_items += 1
                        total_unreferenced_content_bytes += content_bytes
                        total_unreferenced_stored_bytes += stored_bytes
    return BRSS(total_references, total_referenced_items, total_referenced_content_bytes, total_referenced_stored_bytes, total_unreferenced_items, total_unreferenced_content_bytes, total_unreferenced_stored_bytes)

def get_repo_storage_stats_list():
    from . import config
    return [(repo_name, get_repo_storage_stats(repo_name)) for repo_name in config.get_repo_name_list()]

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
import errno
import sys
import re

from . import excpns

HOME_DIR = os.path.expanduser("~")
absolute_path = lambda path: os.path.abspath(os.path.expanduser(path))
relative_path = lambda path: os.path.relpath(absolute_path(path))
path_rel_home = lambda path: os.path.relpath(absolute_path(path), HOME_DIR)

class FStatsMixin:
    @property
    def is_dir(self):
        return stat.S_ISDIR(self.attributes.st_mode)
    @property
    def is_hard_linked(self):
        return self.attributes.st_nlink > 1
    @property
    def is_soft_link(self):
        return stat.S_ISLNK(self.attributes.st_mode)
    @property
    def is_reg_file(self):
        return stat.S_ISREG(self.attributes.st_mode)
    @property
    def mode(self):
        return self.attributes.st_mode
    @property
    def mtime(self):
        return self.attributes.st_mtime
    @property
    def nlink(self):
        return self.attributes.st_nlink
    @property
    def size(self):
        return self.attributes.st_size
    @property
    def uid(self):
        return self.attributes.st_uid
    @property
    def gid(self):
        return self.attributes.st_gid
    @property
    def inode(self):
        return self.attributes.st_ino
    @property
    def device(self):
        return self.attributes.st_dev

class SFile(collections.namedtuple("SFile", ["path", "attributes", "payload", "blob_repo_data"]), FStatsMixin):
    @property
    def link_tgt(self):
        return self.payload if stat.S_ISLNK(self.attributes.st_mode) else None
    @property
    def hex_digest(self):
        return self.payload if stat.S_ISREG(self.attributes.st_mode) else None
    def open_read_only(self):
        from . import blobs
        if not stat.S_ISREG(self.attributes.st_mode):
            raise excpns.NotRegularFile(self.path)
        with blobs.open_blob_repo(self.blob_repo_data, writeable=True) as blob_mgr:
            return blob_mgr.open_blob_read_only(self.payload)

class SsStats(collections.namedtuple("SsStats", ["nfiles", "nlinks", "content_size"])):
    def __add__(self, other):
        return SsStats(self.nfiles + other.nfiles, self.nlinks + other.nlinks, self.content_size + other.content_size)

class Snapshot(object):
    def __init__(self, parent=None, attributes=None):
        self.parent = parent
        self.attributes = attributes
        self.subdirs = {}
        self.files = {}
    def _add_subdir(self, path_parts, attributes=None):
        name = path_parts[0]
        if len(path_parts) == 1:
            # neeed to be careful that we don't clobber existing data
            if name not in self.subdirs:
                self.subdirs[name] = Snapshot(self, attributes)
            elif self.subdirs[name].attributes is None:
                # cover the case where it was previously created an way to a leaf dir
                self.subdirs[name].attributes = attributes
            return self.subdirs[name]
        else:
            if name not in self.subdirs:
                self.subdirs[name] = Snapshot(self)
            return self.subdirs[name]._add_subdir(path_parts[1:], attributes)
    def add_subdir(self, dir_path, attributes=None):
        return self._add_subdir(dir_path.strip(os.sep).split(os.sep), attributes)
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
    def find_file(self, file_path, blob_repo_data):
        dir_path, file_name = os.path.split(file_path)
        data = self.find_dir(dir_path).files[file_name]
        return SFile(file_path, data[0], data[1], blob_repo_data)
    def iterate_hex_digests(self):
        for data in self.files.values():
            if stat.S_ISREG(data[0].st_mode):
                yield data[1]
        for subdir in self.subdirs.values():
            for hex_digest in subdir.iterate_hex_digests():
                yield hex_digest
    def get_statistics(self):
        statistics = SsStats(0, 0, 0)
        for data in self.files.values():
            if stat.S_ISREG(data[0].st_mode):
                statistics += SsStats(1, 0, data[0].st_size)
            else:
                statistics += SsStats(0, 1, 0)
        for subdir in self.subdirs.values():
            statistics += subdir.get_statistics()
        return statistics

def read_snapshot(snapshot_file_path):
    import cPickle
    if snapshot_file_path.endswith(".gz"):
        import gzip
        fobj = gzip.open(snapshot_file_path, "rb")
    else:
        fobj = open(snapshot_file_path, "rb")
    return cPickle.load(fobj)

# NB: make sure that these two are in concert
_SNAPSHOT_FILE_NAME_TEMPLATE = "%Y-%m-%d-%H-%M-%S.pkl"
_SNAPSHOT_FILE_NAME_CRE = re.compile("\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.pkl(\.gz)?")
ss_root = lambda fname: fname.split(".")[0]

def write_snapshot(snapshot_dir_path, snapshot, permissions=stat.S_IRUSR|stat.S_IRGRP):
    import cPickle
    import time
    snapshot_file_name = time.strftime(_SNAPSHOT_FILE_NAME_TEMPLATE, time.gmtime())
    snapshot_file_path = os.path.join(snapshot_dir_path, snapshot_file_name)
    if snapshot_file_path.endswith(".gz"):
        import gzip
        fobj = gzip.open(snapshot_file_path, "wb")
    else:
        fobj = open(snapshot_file_path, "wb")
    cPickle.dump(snapshot, fobj)
    os.chmod(snapshot_file_path, permissions)
    return os.path.getsize(snapshot_file_path)

def read_most_recent_snapshot(snapshot_dir_path):
    candidates = [f for f in os.listdir(snapshot_dir_path) if _SNAPSHOT_FILE_NAME_CRE.match(f)]
    if candidates:
        return read_snapshot(os.path.join(snapshot_dir_path, sorted(candidates, reverse=True)[0]))
    return Snapshot()

def get_snapshot_file_list(snapshot_dir_path, reverse=False):
    return sorted([f for f in os.listdir(snapshot_dir_path) if _SNAPSHOT_FILE_NAME_CRE.match(f)], reverse=reverse)

SnapshotStats = collections.namedtuple("SnapshotStats", ["file_count", "soft_link_count", "content_bytes", "adj_content_bytes"])

class _SnapshotGenerator(object):
    # The file has gone away
    FORGIVEABLE_ERRNOS = frozenset((errno.ENOENT, errno.ENXIO))
    def __init__(self, blob_mgr, exclude_dir_res, exclude_file_res, prior_snapshot=None, skip_broken_links=False, stderr=sys.stderr):
        self._snapshot = Snapshot()
        self.skip_broken_links=skip_broken_links
        self.blob_mgr = blob_mgr
        self.prior_snapshot = prior_snapshot if prior_snapshot else Snapshot()
        self.content_count = 0
        self.adj_content_count = 0
        self.file_count = 0
        self.soft_link_count = 0
        self._exclude_dir_cres = exclude_dir_res
        self._exclude_file_cres = exclude_file_res
        #self._extant_hex_digests = list()
    @property
    def snapshot(self):
        return self._snapshot
    @property
    def statistics(self):
        return SnapshotStats(self.file_count, self.soft_link_count, self.content_count, self.adj_content_count)
    def _include_file(self, files, file_name, file_path, prior_files):
        # NB. redundancy in file_name and file_path is deliberate
        # let the caller handle OSError exceptions
        file_stats = os.lstat(file_path)
        if stat.S_ISREG(file_stats.st_mode):
            prior_file = prior_files.get(file_name, None)
            if prior_file and (prior_file[0].st_size == file_stats.st_size) and (prior_file[0].st_mtime == file_stats.st_mtime):
                hex_digest = prior_file[1]
                #self._extant_hex_digests.append(hex_digest)
                self.blob_mgr.incr_ref_count(hex_digest)
            else:
                hex_digest = self.blob_mgr.store_contents(file_path)
            self.content_count += file_stats.st_size
            self.adj_content_count += file_stats.st_size / file_stats.st_nlink
            self.file_count += 1
            files[file_name] = (file_stats, hex_digest)
        elif stat.S_ISLNK(file_stats.st_mode):
            target_file_path = os.readlink(file_path)
            if self.skip_broken_links and not os.path.exists(target_file_path):
                stderr.write("{0} -> {1} symbolic link is broken.  Skipping.\n".format(file_path, target_file_path))
                return
            self.soft_link_count += 1
            files[file_name] = (file_stats, target_file_path)
    def include_dir(self, abs_dir_path):
        for dir_path, subdir_paths, file_names in os.walk(abs_dir_path, followlinks=False):
            if self.is_excluded_dir(dir_path):
                continue
            files = self._snapshot.add_subdir(dir_path, os.lstat(dir_path)).files
            prior_dir = self.prior_snapshot.find_dir(dir_path)
            prior_files = {} if prior_dir is None else prior_dir.files
            for file_name in file_names:
                # NB: checking both name AND full path of file for exclusion
                if self.is_excluded_file(file_name):
                    continue
                file_path = os.path.join(dir_path, file_name)
                if self.is_excluded_file(file_path):
                    continue
                try:
                    self._include_file(files, file_name, file_path, prior_files)
                except OSError as edata:
                    # race condition
                    if edata.errno in self.FORGIVEABLE_ERRNOS:
                        continue # it's gone away so we skip it
                    raise edata # something we can't handle so throw the towel in
            excluded_subdir_paths = [subdir_path for subdir_path in subdir_paths if self.is_excluded_dir(subdir_path)]
            # NB: this is an in place reduction in the list of subdirectories
            for esdp in excluded_subdir_paths:
                subdir_paths.remove(esdp)
    def include_file(self, abs_file_path):
        # NB: no exclusion checks as explicit inclusion trumps exclusion
        abs_dir_path, file_name = os.path.split(abs_file_path)
        files = self._snapshot.add_subdir(abs_dir_path, os.lstat(abs_dir_path)).files
        prior_dir = self.prior_snapshot.find_dir(abs_dir_path)
        prior_files = {} if prior_dir is None else prior_dir.files
        try:
            self._include_file(files, file_name, abs_file_path, prior_files)
        except OSError as edata:
            # race condition
            if edata.errno not in self.FORGIVEABLE_ERRNOS:
                raise edata # something we can't handle so throw the towel in
    def is_excluded_file(self, file_path_or_name):
        for cre in self._exclude_file_cres:
            if cre.match(file_path_or_name):
                return True
        return False
    def is_excluded_dir(self, dir_path_or_name):
        for cre in self._exclude_dir_cres:
            if cre.match(dir_path_or_name):
                return True
        return False
    def update_ref_counts(self):
        pass
        #self.blob_mgr.incr_ref_counts(self._extant_hex_digests)

def generate_snapshot(archive, use_previous=True, stderr=sys.stderr):
    import time
    from . import blobs
    start_time = time.clock()
    previous_snapshot = read_most_recent_snapshot(archive.snapshot_dir_path) if use_previous else None
    blob_repo_data = blobs.get_blob_repo_data(archive.repo_name)
    with blobs.open_blob_repo(blob_repo_data, writeable=True) as blob_mgr:
        snapshot_generator = _SnapshotGenerator(blob_mgr, archive.exclude_dir_res, archive.exclude_file_res, previous_snapshot, archive.skip_broken_soft_links, stderr=stderr)
        try:
            for item in archive.includes:
                abs_item = absolute_path(item)
                if os.path.isdir(abs_item):
                    snapshot_generator.include_dir(abs_item)
                elif os.path.isfile(abs_item):
                    snapshot_generator.include_file(abs_item)
                elif os.path.exists(abs_item):
                    stderr.write(_("{0}: is not a file or directory. Skipped.").format(item))
                else:
                    stderr.write(_("{0}: not found. Skipped.").format(item))
            snapshot_generator.update_ref_counts()
            snapshot_size = write_snapshot(archive.snapshot_dir_path, snapshot_generator.snapshot)
        finally:
            elapsed_time = time.clock() - start_time
        return (snapshot_generator.statistics, snapshot_size, elapsed_time)

class SnapshotFS(collections.namedtuple("SnapshotFS", ["path", "archive_name", "snapshot_name", "snapshot", "blob_repo_data"]), FStatsMixin):
    @property
    def attributes(self):
        return self.snapshot.attributes
    @property
    def name(self):
        return os.path.basename(self.path)
    def get_file(self, file_path):
        abs_file_path = absolute_path(file_path)
        try:
            file_data = self.snapshot.find_file(abs_file_path, self.blob_repo_data)
        except (KeyError, AttributeError):
            raise excpns.FileNotFound(file_path, self.archive_name, ss_root(self.snapshot_name))
        return file_data
    def get_subdir(self, subdir_path):
        if subdir_path == os.sep:
            return self
        abs_subdir_path = absolute_path(subdir_path)
        subdir_ss = self.snapshot.find_dir(abs_subdir_path)
        if not subdir_ss:
            raise excpns.DirNotFound(subdir_path, self.archive_name, ss_root(self.snapshot_name))
        return SnapshotFS(subdir_path, self.archive_name, self.snapshot_name, subdir_ss, self.blob_repo_data)
    def iterate_subdirs(self, pre_path=False, recurse=False):
        if not isinstance(pre_path, str):
            pre_path = self.path if pre_path is True else ""
        for subdir_name, ss_snapshot in self.snapshot.subdirs.items():
            snapshot_fs = SnapshotFS(os.path.join(pre_path, subdir_name), self.archive_name, self.snapshot_name, ss_snapshot, self.blob_repo_data)
            yield snapshot_fs
            if recurse:
                for r_snapshot_fs in snapshot_fs.iterate_subdirs(pre_path=True, recurse=True):
                    yield r_snapshot_fs
    def iterate_files(self, pre_path=False, recurse=False):
        if not isinstance(pre_path, str):
            pre_path = self.path if pre_path is True else ""
        for file_name, data in self.snapshot.files.items():
            yield SFile(os.path.join(pre_path, file_name), data[0], data[1], self.blob_repo_data)
        if recurse:
            for subdir in self.iterate_subdirs():
                for sfile in subdir.iterate_files(pre_path=os.path.join(pre_path, subdir.name), recurse=recurse):
                    yield sfile

def get_snapshot_fs(archive_name, seln_fn=lambda l: l[-1]):
    from . import config
    from . import blobs
    archive = config.read_archive_spec(archive_name)
    snapshot_names = get_snapshot_file_list(archive.snapshot_dir_path)
    if not snapshot_names:
        raise excpns.EmptyArchive(archive_name)
    try:
        snapshot_name = seln_fn(snapshot_names)
    except:
        raise excpns.NoMatchingSnapshot([ss_root(ss_name) for ss_name in snapshot_names])
    snapshot = read_snapshot(os.path.join(archive.snapshot_dir_path, snapshot_name))
    blob_repo_data = blobs.get_blob_repo_data(archive.repo_name)
    return SnapshotFS(os.sep, archive_name, snapshot_name, snapshot, blob_repo_data)

def delete_snapshot(archive_name, seln_fn=lambda l: l[-1], clear_fell=False):
    from . import config
    from . import blobs
    archive = config.read_archive_spec(archive_name)
    snapshot_names = get_snapshot_file_list(archive.snapshot_dir_path)
    if not snapshot_names:
        raise excpns.EmptyArchive(archive_name)
    try:
        snapshot_name = seln_fn(snapshot_names)
    except:
        raise excpns.NoMatchingSnapshot([ss_root(ss_name) for ss_name in snapshot_names])
    if not clear_fell and len(snapshot_names) == 1:
        raise excpns.LastSnapshot(archive_name, ss_root(snapshot_name))
    snapshot_file_path = os.path.join(archive.snapshot_dir_path, snapshot_name)
    snapshot = read_snapshot(snapshot_file_path)
    blob_repo_data = blobs.get_blob_repo_data(archive.repo_name)
    with blobs.open_blob_repo(blob_repo_data, writeable=True) as blob_mgr:
        os.remove(snapshot_file_path)
        blob_mgr.release_contents(snapshot.iterate_hex_digests())

def get_snapshot_list(archive_name, reverse=False):
    from . import config
    archive = config.read_archive_spec(archive_name)
    ss_list = []
    for snapshot_name in get_snapshot_file_list(archive.snapshot_dir_path, reverse=reverse):
        snapshot_file_path = os.path.join(archive.snapshot_dir_path, snapshot_name)
        snapshot_size = os.path.getsize(snapshot_file_path)
        snapshot_stats = read_snapshot(snapshot_file_path).get_statistics()
        ss_list.append((ss_root(snapshot_name), snapshot_size, snapshot_stats))
    return ss_list
    #return [ss_root(ss_name) for ss_name in get_snapshot_file_list(archive.snapshot_dir_path, reverse=reverse)]

def create_new_archive(archive_name, location_dir_path, repo_spec, includes, exclude_dir_res=None, exclude_file_res=None, skip_broken_sl=True):
    from . import config
    base_dir_path = config.write_archive_spec(
        archive_name=archive_name,
        location_dir_path=location_dir_path,
        repo_name=repo_spec.name,
        includes=includes,
        exclude_dir_res=exclude_dir_res if exclude_dir_res else [],
        exclude_file_res=exclude_file_res if exclude_file_res else [],
        skip_broken_sl=skip_broken_sl
    )
    try:
        os.makedirs(base_dir_path)
    except EnvironmentError as edata:
        config.delete_archive_spec(archive_name)
        if edata.errno == errno.EEXIST:
            raise excpns.SnapshotArchiveLocationExists(archive_name)
        elif edata.errno == errno.EPERM:
            raise excpns.SnapshotArchiveLocationNoPerm(archive_name)
        else:
            raise edata

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

class SFile(collections.namedtuple("SFile", ["path", "fstats", "payload"]), FStatsMixin):
    @property
    def link_tgt(self):
        return seld.payload if stat.S_ISLNK(self.fstats.st_mode) else None
    @property
    def hex_digest(self):
        return seld.payload if stat.S_ISREG(self.fstats.st_mode) else None

class Snapshot(object):
    def __init__(self, parent=None, dir_stats=None):
        self.parent = parent
        self.dir_stats = dir_stats
        self.subdirs = {}
        self.files = {}
    def _add_subdir(self, path_parts, dir_stats=None):
        name = path_parts[0]
        if len(path_parts) == 1:
            # neeed to be careful that we don't clobber existing data
            if name not in self.subdirs:
                self.subdirs[name] = Snapshot(self, dir_stats)
            elif self.subdirs[name].dir_stats is None:
                # cover the case where it was previously created an way to a leaf dir
                self.subdirs[name].dir_stats = dir_stats
            return self.subdirs[name]
        else:
            if name not in self.subdirs:
                self.subdirs[name] = Snapshot(self)
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
    def get_file(self, file_path):
        dir_path, file_name = os.path.split(file_path)
        data = self.find_dir(dir_path).files[file_name]
        return SFile(file_path, data[0], data[1])
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

# NB: make sure that these two are in concert
_SNAPSHOT_FILE_NAME_TEMPLATE = "%Y-%m-%d-%H-%M-%S.pkl"
_SNAPSHOT_FILE_NAME_CRE = re.compile("\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.pkl(\.gz)?")

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

def get_snapshot_list(snapshot_dir_path, reverse=False):
    return sorted([f for f in os.listdir(snapshot_dir_path) if _SNAPSHOT_FILE_NAME_CRE.match(f)], reverse=reverse)

SnapshotStats = collections.namedtuple("SnapshotStats", ["file_count", "soft_link_count", "content_bytes", "adj_content_bytes"])

class _SnapshotGenerator(object):
    # The file has gone away
    FORGIVEABLE_ERRNOS = frozenset((errno.ENOENT, errno.ENXIO))
    def __init__(self, blob_mgr, exclude_dir_cres, exclude_file_cres, prior_snapshot=None, skip_broken_links=False):
        self._snapshot = Snapshot()
        self.skip_broken_links=skip_broken_links
        self.blob_mgr = blob_mgr
        self.prior_snapshot = prior_snapshot if prior_snapshot else Snapshot()
        self.content_count = 0
        self.adj_content_count = 0
        self.file_count = 0
        self.soft_link_count = 0
        self._exclude_dir_cres = exclude_dir_cres
        self._exclude_file_cres = exclude_file_cres
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
            else:
                hex_digest = self.blob_mgr.store_contents(file_path)
            self.content_count += file_stats.st_size
            self.adj_content_count += file_stats.st_size / file_stats.st_nlink
            self.file_count += 1
            files[file_name] = (file_stats, hex_digest)
        elif stat.S_ISLNK(file_stats.st_mode):
            target_file_path = os.readlink(file_path)
            if self.skip_broken_links and not os.path.exists(target_file_path):
                sys.stderr.write("{0} -> {1} symbolic link is broken.  Skipping.\n".format(file_path, target_file_path))
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

def generate_snapshot(archive, stderr=sys.stderr):
    import time
    from . import blobs
    start_time = time.clock()
    previous_snapshot = read_most_recent_snapshot(archive.snapshot_dir_path)
    blob_mgr = blobs.open_repo(archive.repo_name)
    snapshot_generator = _SnapshotGenerator(blob_mgr, archive.exclude_dir_cres, archive.exclude_file_cres, previous_snapshot, archive.skip_broken_soft_links)
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
        snapshot_size = write_snapshot(archive.snapshot_dir_path, snapshot_generator.snapshot)
    finally:
        elapsed_time = time.clock() - start_time
    return (snapshot_generator.statistics, snapshot_size, elapsed_time)

class SnapshotFS(object):
    def __init__(self, archive_name, seln_fn=lambda l: l[-1]):
        from . import config
        from . import blobs
        self.archive_name = archive_name
        try:
            self._archive = config.read_archive_spec(archive_name)
        except IOError:
            raise excpns.UnknownSnapshotArchive(archive_name)
        snapshot_names = get_snapshot_list(self._archive.snapshot_dir_path)
        if not snapshot_names:
            raise excpns.EmptyArchive(archive_name)
        self.snapshot_name = seln_fn(snapshot_names)
        self._snapshot = read_snapshot(os.path.join(self._archive.snapshot_dir_path, self.snapshot_name))
        self._blob_mgr = blobs.open_repo(self._archive.repo_name)
    def cat_file(self, file_path, stdout=sys.stdout):
        abs_file_path = absolute_path(file_path)
        try:
            file_data = self._snapshot.get_file(abs_file_path)
        except (KeyError, AttributeError):
            raise excpns.NotFoundInSnapshot(file_path, self.archive_name, self.snapshot_name)
        if file_data.is_link:
            stdout.write("LINK: {0} -> {1}\n".format(file_path, file_data.link_tgt))
        else:
            contents = self._blob_mgr.fetch_contents(file_data.payload)
            for line in contents.splitlines(True):
                stdout.write(line)

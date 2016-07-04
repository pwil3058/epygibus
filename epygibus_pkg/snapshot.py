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

import os
import collections
import stat
import errno
import sys
import re
import io

from .w2and3 import pickle, PICKLE_PROTOCOL

from . import excpns
from . import bmark
from . import utils

HOME_DIR = os.path.expanduser("~")
absolute_path = lambda path: os.path.abspath(os.path.expanduser(path))
relative_path = lambda path: os.path.relpath(absolute_path(path))
path_rel_home = lambda path: os.path.relpath(absolute_path(path), HOME_DIR)

# indices of fields in iterable version of os.lstat() output
# NB: storing this data as tuple() to aid Python 2/3 compatibility
NFIELDS = 10
MODE_I, INO_I, DEV_I, NLINK_I, UID_I, GID_I, SIZE_I, ATIME_I, MTIME_I, CTIME_I = range(NFIELDS)
ATTR_TUPLE = lambda attributes: tuple(attributes[:NFIELDS])
get_attr_tuple = lambda path: ATTR_TUPLE(os.lstat(path))
# a named tuple for passing around the data (if needed)
# use the same names os.lstat() output for interchangeability
ATTRS_NAMED = collections.namedtuple("ATTRS_NAMED", ["st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid", "st_size", "st_atime", "st_mtime", "st_ctime"])

class PathComponentsMixin:
    @property
    def name(self):
        return os.path.basename(self.path)
    @property
    def dir_path(self):
        return os.path.dirname(self.path)

class SFile(collections.namedtuple("SFile", ["path", "attributes", "content_token", "repo_mgmt_key"]), PathComponentsMixin):
    def open_read_only(self, binary=False):
        from . import repo
        with repo.open_repo_mgr(self.repo_mgmt_key, writeable=True) as repo_mgr:
            return repo_mgr.open_contents_read_only(self.content_token, binary=binary)
    def copy_contents_to(self, target_file_path, overwrite=False):
        from . import repo
        if not overwrite and os.path.isfile(target_file_path):
            raise excpns.FileOverwriteError(target_file_path)
        with repo.open_repo_mgr(self.repo_mgmt_key, writeable=False) as repo_mgr:
            repo_mgr.copy_contents_to(self.content_token, target_file_path, self.attributes)
    def get_content_storage_stats(self):
        from . import repo
        with repo.open_repo_mgr(self.repo_mgmt_key, writeable=True) as repo_mgr:
            return repo_mgr.get_content_storage_stats(self.content_token)
    @property
    def is_hard_linked(self):
        return self.attributes.st_nlink > 1
    @classmethod
    def make(cls, path, f_data, repo_mgmt_key):
        return cls(path, ATTRS_NAMED(*f_data[0]), f_data[1], repo_mgmt_key)

class SLink(collections.namedtuple("SLink", ["path", "attributes", "tgt_path"]), PathComponentsMixin):
    def create_link(self, orig_curdir, stderr):
        try:
            #if the file exists we have to remove it or get stat.EEXIST error
            if os.path.islink(self.path) or os.path.isfile(self.path):
                os.remove(self.path)
            elif os.path.isdir(self.path):
                import shutil
                shutil.rmtree(self.path)
            if utils.is_rel_path(self.tgt_path):
                os.chdir(self.dir_path)
                try:
                    os.symlink(self.tgt_path, self.path)
                finally:
                    os.chdir(orig_curdir)
            else:
                os.symlink(self.tgt_path, self.path)
            try:
                os.lchmod(self.path, self.attributes.st_mode)
            except AttributeError:
                # NB: some systems don't support lchmod())
                os.chmod(self.path, self.attributes.st_mode)
            os.lchown(self.path, self.attributes.st_uid, self.attributes.st_gid)
            return 1
        except EnvironmentError as edata:
            # report the error and move on (we have permission to wreak havoc)
            stderr.write(_("Error: {}: {}\n").format(edata.strerror, edata.filename))
            return 0
    @classmethod
    def make(cls, path, f_data):
        return cls(path, ATTRS_NAMED(*f_data[0]), f_data[1])

# TODO: "nreleased_items" to be ditched for "ncitems" (nothing is released)
class CreationStats(collections.namedtuple("CreationStats", ["file_count", "soft_link_count", "content_bytes", "nnew_items", "nreleased_citems", "etd"])):
    def __add__(self, other):
        return CreationStats(*[self[i] + other[i] for i in range(len(self))])

class Snapshot(object):
    def __init__(self, parent=None, attributes=None):
        self.parent = parent
        self.attributes = attributes
        self.subdirs = {}
        self.files = {}
        self.file_links = {}
        self.subdir_links = {}
    def _find_or_add_subdir(self, path_parts, index, attributes):
        name = path_parts[index]
        if index == len(path_parts) - 1:
            # neeed to be careful that we don't clobber existing data
            if name not in self.subdirs:
                self.subdirs[name] = Snapshot(self, attributes)
            return self.subdirs[name]
        else:
            if name not in self.subdirs:
                subdir_attributes = get_attr_tuple(os.path.join(os.sep, *path_parts[:index+1]))
                self.subdirs[name] = Snapshot(self, subdir_attributes)
            return self.subdirs[name]._find_or_add_subdir(path_parts, index + 1, attributes)
    def find_or_add_subdir(self, abs_subdir_path):
        attributes = get_attr_tuple(abs_subdir_path)
        return self._find_or_add_subdir(abs_subdir_path.strip(os.sep).split(os.sep), 0, attributes)
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
    def find_file(self, file_path, repo_mgmt_key):
        dir_path, file_name = os.path.split(file_path)
        return SFile.make(file_path, self.find_dir(dir_path).files[file_name], repo_mgmt_key)
    def find_file_link(self, file_path):
        dir_path, file_name = os.path.split(file_path)
        return SLink.make(file_path, self.find_dir(dir_path).file_links[file_name])
    def find_subdir_link(self, subdir_path):
        dir_path, subdir_name = os.path.split(subdir_path)
        return SLink.make(subdir_path, self.find_dir(dir_path).subdir_links[subdir_name])
    def iterate_content_tokens(self):
        for _dont_care, content_token in self.files.values():
            yield content_token
        for subdir in self.subdirs.values():
            for content_token in subdir.iterate_content_tokens():
                yield content_token

class SnapshotPlus(object):
    # limit the number of none basic python types to future proof
    def __init__(self, snapshot, statistics):
        self.snapshot = snapshot
        self._statistics = tuple(statistics[0:-1])
        self._time_statistics = tuple(statistics[-1][0:])
    @property
    def creation_stats(self):
        return CreationStats(*(self._statistics + (self.time_statistics,)))
    @property
    def time_statistics(self):
        return bmark.ETD(*self._time_statistics)
    @property
    def subdirs(self):
        return self.snapshot.subdirs
    @property
    def files(self):
        return self.snapshot.files
    @property
    def subdir_links(self):
        return self.snapshot.subdir_links
    @property
    def file_links(self):
        return self.snapshot.file_links
    def find_dir(self, dir_path):
        return self.snapshot.find_dir(dir_path)
    def find_file(self, file_path, repo_mgmt_key):
        return self.snapshot.find_file(file_path, repo_mgmt_key)
    def find_subdir_link(self, dir_path):
        return self.snapshot.find_subdir_link(dir_path)
    def find_file_link(self, file_path):
        return self.snapshot.find_file_link(file_path)
    def iterate_content_tokens(self):
        return self.snapshot.iterate_content_tokens()

def read_snapshot(snapshot_file_path):
    if snapshot_file_path.endswith(".gz"):
        import gzip
        fobj = gzip.open(snapshot_file_path, "rb")
    else:
        fobj = io.open(snapshot_file_path, "rb")
    return pickle.load(fobj)

# NB: make sure that these two are in concert
_SNAPSHOT_FILE_NAME_TEMPLATE = "%Y-%m-%d-%H-%M-%S.pkl"
SNAPSHOT_NAME_CRE = re.compile("(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})")
SNAPSHOT_WC_NAME_CRE = re.compile("(\d{4}|.)-(\d{2}|.)-(\d{2}|.)(-(\d{2}|.)(-(\d{2})(-(\d{2}))?)?)?")
_SNAPSHOT_FILE_NAME_CRE = re.compile("\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.pkl(\.gz)?")
ss_root = lambda fname: os.path.basename(fname).split(".")[0]
_Y, _MO, _D, _DC0, _H, _DC1, _MI, _DC2, _S = range(9)

def validate_snapshot_name(name):
    import datetime
    m = SNAPSHOT_NAME_CRE.match(name)
    if not m:
        return False
    numbers = [int(n) for n in m.groups()]
    try:
        date = datetime.date(*numbers[:3])
    except ValueError:
        return False
    return numbers[3] < 24 and numbers[4] < 60 and numbers[5] < 60

def expand_snapshot_wc_name(wc_name):
    import time
    m = SNAPSHOT_WC_NAME_CRE.match(wc_name)
    if not m:
        raise ValueError
    now = time.strftime("%Y%m%d%H", time.gmtime())
    groups = m.groups()
    name = now[:4] if groups[_Y] == "." else groups[_Y]
    name += "-" + (now[4:6] if groups[_MO] == "." else groups[_MO])
    name += "-" + (now[6:8] if groups[_D] == "." else groups[_D])
    name += "-" + (now[8:10] if groups[_H] == "." else "00" if groups[_H] is None else groups[_H])
    name += "-" + ("00" if groups[_MI] is None else groups[_MI])
    name += "-" + ("00" if groups[_S] is None else groups[_S])
    if not validate_snapshot_name(name):
        raise ValueError
    return name

def read_most_recent_snapshot(snapshot_dir_path):
    candidates = [f for f in os.listdir(snapshot_dir_path) if _SNAPSHOT_FILE_NAME_CRE.match(f)]
    if candidates:
        return read_snapshot(os.path.join(snapshot_dir_path, sorted(candidates, reverse=True)[0]))
    return Snapshot()

def _get_snapshot_file_list(snapshot_dir_path, reverse=False):
    return sorted([f for f in os.listdir(snapshot_dir_path) if _SNAPSHOT_FILE_NAME_CRE.match(f)], reverse=reverse)

class SnapshotGenerator(object):
    # The file has gone away
    FORGIVEABLE_ERRNOS = frozenset((errno.ENOENT, errno.ENXIO))
    def __init__(self, archive, stderr=sys.stderr, report_skipped_links=False):
        import re
        import fnmatch
        from . import repo
        from . import bmark
        self._use_gmt = False # TODO: make this an option
        self._archive = archive
        self._exclude_dir_cres = [re.compile(fnmatch.translate(os.path.expanduser(glob))) for glob in archive.exclude_dir_globs]
        self._exclude_file_cres = [re.compile(fnmatch.translate(os.path.expanduser(glob))) for glob in archive.exclude_file_globs]
        self.report_skipped_links=report_skipped_links
        self.repo_mgmt_key = repo.get_repo_mgmt_key(archive.repo_name)
        self.stderr = stderr
        self._reset_counters()
        self._snapshot = None
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, exc_tb):
        if self._snapshot:
            from . import repo
            # there will be no persistent record so release content
            with repo.open_repo_mgr(self.repo_mgmt_key, writeable=True) as repo_mgr:
                repo_mgr.release_contents(self._snapshot.iterate_content_tokens())
    def _reset_counters(self):
        self.content_count = 0
        self.file_count = 0
        self.file_slink_count = 0
        self.subdir_slink_count = 0
        self.released_items = 0
        self.created_items = 0
    def _adjust_item_stats(self, start_counts, end_counts):
        # TODO: check the maths here (use a namedtuple)
        self.created_items += max(sum(end_counts[:-1]) - sum(start_counts[:-1]), 0)
        self.released_items += max(end_counts[1] - start_counts[1], 0)
    @property
    def creation_stats(self):
        return CreationStats(self.file_count, self.file_slink_count + self.subdir_slink_count, self.content_count, self.created_items, self.released_items, self.elapsed_time.get_etd())
    def _include_file(self, subdir_ss, file_name, file_path, repo_mgr):
        # NB. redundancy in file_name and file_path is deliberate
        # let the caller handle OSError exceptions
        if file_name in subdir_ss.files: # already included via another "includes" entry
            # NB multiple inclusion would mess with content management reference counts
            return
        try: # it's possible content manager got environment error reading file, if so skip it and report
            content_token = repo_mgr.store_contents(file_path)
        except EnvironmentError as edata:
            self.stderr.write(_("Error: saving \"{}\" content failed: {}. Skipping.\n").format(file_path, edata.strerror))
            return
        file_attrs = get_attr_tuple(file_path)
        self.content_count += file_attrs[SIZE_I]
        self.file_count += 1
        subdir_ss.files[file_name] = (file_attrs, content_token)
    def _include_file_link(self, subdir_ss, file_name, file_path):
        # NB. redundancy in file_name and file_path is deliberate
        # let the caller handle OSError exceptions
        # NB don't check for previous inclusion as no harm done
        target_path = os.readlink(file_path)
        abs_target_path = utils.get_link_abs_path(target_path, file_path)
        target_valid = os.path.isfile(abs_target_path)
        if self._archive.skip_broken_soft_links and not target_valid:
            if self.report_skipped_links:
                self.stderr.write("{0} -> {1} symbolic link is broken.  Skipping.\n".format(file_path, target_path))
            return None
        self.file_slink_count += 1
        subdir_ss.file_links[file_name] = (get_attr_tuple(file_path), target_path)
        return abs_target_path if target_valid else None
    def _include_subdir_link(self, subdir_ss, file_name, file_path):
        # NB. redundancy in file_name and file_path is deliberate
        # let the caller handle OSError exceptions
        # NB don't check for previous inclusion as no harm done
        target_path = os.readlink(file_path)
        abs_target_path = utils.get_link_abs_path(target_path, file_path)
        target_valid = os.path.isdir(abs_target_path)
        if self._archive.skip_broken_soft_links and not target_valid:
            if self.report_skipped_links:
                self.stderr.write("{0} -> {1} symbolic link is broken.  Skipping.\n".format(file_path, target_path))
            return None
        self.subdir_slink_count += 1
        subdir_ss.subdir_links[file_name] = (get_attr_tuple(file_path), target_path)
        return abs_target_path if target_valid else None
    def _include_dir(self, abs_base_dir_path):
        from . import repo
        with repo.open_repo_mgr(self.repo_mgmt_key, writeable=True) as repo_mgr:
            start_counts = repo_mgr.get_counts()
            for abs_dir_path, subdir_names, file_names in os.walk(abs_base_dir_path, followlinks=True):
                if self.is_excluded_dir(abs_dir_path):
                    continue
                new_subdir_ss = self._snapshot.find_or_add_subdir(abs_dir_path)
                for file_name in file_names:
                    # NB: checking both name AND full path of file for exclusion
                    if self.is_excluded_file(file_name):
                        continue
                    file_path = os.path.join(abs_dir_path, file_name)
                    if self.is_excluded_file(file_path):
                        continue
                    try:
                        if os.path.islink(file_path):
                            self._include_file_link(new_subdir_ss, file_name, file_path)
                        else:
                            self._include_file(new_subdir_ss, file_name, file_path, repo_mgr)
                    except OSError as edata:
                        # race condition
                        if edata.errno in self.FORGIVEABLE_ERRNOS:
                            continue # it's gone away so we skip it
                        raise edata # something we can't handle so throw the towel in
                excluded_subdir_names = []
                for subdir_name in subdir_names:
                    if self.is_excluded_dir(subdir_name):
                        excluded_subdir_names.append(subdir_name)
                        continue
                    abs_subdir_path = os.path.join(abs_dir_path, subdir_name)
                    if self.is_excluded_dir(abs_subdir_path):
                        excluded_subdir_names.append(subdir_name)
                        continue
                    if os.path.islink(abs_subdir_path):
                        excluded_subdir_names.append(subdir_name)
                        try:
                            self._include_subdir_link(new_subdir_ss, subdir_name, abs_subdir_path)
                        except OSError as edata:
                            # race condition
                            if edata.errno in self.FORGIVEABLE_ERRNOS:
                                continue # it's gone away so we skip it
                            raise edata # something we can't handle so throw the towel in
                # NB: this is an in place reduction in the list of subdirectories
                for esdp in excluded_subdir_names:
                    subdir_names.remove(esdp)
            self._adjust_item_stats(start_counts, repo_mgr.get_counts())
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
    def generate_snapshot(self):
        from . import repo
        start_time = bmark.get_os_times()
        self._reset_counters()
        if self._snapshot is not None:
            # it hasn't been written and there will be no persistent record so release content
            with repo.open_repo_mgr(self.repo_mgmt_key, writeable=True) as repo_mgr:
                repo_mgr.release_contents(self._snapshot.iterate_content_tokens())
            self._snapshot = None
        self._snapshot = Snapshot()
        abs_dir_link_target_paths = []
        abs_file_link_target_paths = []
        for item in self._archive.includes:
            abs_item_path = absolute_path(item)
            if os.path.islink(abs_item_path):
                # NB: no exclusion checks as explicit inclusion trumps exclusion
                abs_dir_path, file_name = os.path.split(abs_item_path)
                try:
                    subdir_ss = self._snapshot.find_or_add_subdir(abs_dir_path)
                    if os.path.isdir(abs_item_path):
                        abs_target_path = self._include_subdir_link(subdir_ss, file_name, abs_item_path)
                        if abs_target_path:
                            abs_dir_link_target_paths.append(abs_target_path)
                    else:
                        abs_target_path = self._include_file_link(subdir_ss, file_name, abs_item_path)
                        if abs_target_path:
                            abs_file_link_target_paths.append(abs_target_path)
                except EnvironmentError as edata:
                    self.stderr.write(_("Error: processing link {} failed: {}: Skipping.\n").format(abs_item_path, edata.strerror))
            elif os.path.isfile(abs_item_path):
                abs_dir_path, file_name = os.path.split(abs_item_path)
                try:
                    subdir_ss = self._snapshot.find_or_add_subdir(abs_dir_path)
                    with repo.open_repo_mgr(self.repo_mgmt_key, writeable=True) as repo_mgr:
                        start_counts = repo_mgr.get_counts()
                        self._include_file(subdir_ss, file_name, abs_item_path, repo_mgr)
                        self._adjust_item_stats(start_counts, repo_mgr.get_counts())
                except EnvironmentError as edata:
                    self.stderr.write(_("Error: processing file {} failed: {}\n").format(abs_item_path, edata.strerror))
            elif os.path.isdir(abs_item_path):
                try:
                    self._include_dir(abs_item_path)
                except EnvironmentError as edata:
                    self.stderr.write(_("Error: processing directory {} failed: {}\n").format(abs_item_path, edata.strerror))
            elif item == abs_item_path:
                if os.path.exists(abs_item_path):
                    self.stderr.write(_("{0}: is not a file or directory. Skipped.\n").format(item))
                else:
                    self.stderr.write(_("{0}: not found. Skipped.\n").format(item))
            else: # tell them what we thought they meant
                if os.path.exists(abs_item_path):
                    self.stderr.write(_("{0} ({1}): is not a file or directory. Skipped.\n").format(item, abs_item_path))
                else:
                    self.stderr.write(_("{0} ({1}): not found. Skipped.\n").format(item, abs_item_path))
        for abs_item_path in abs_dir_link_target_paths:
            # NB: no point testing for directory existence as mere existence doesn't mean it's fully processed
            try:
                self._include_dir(abs_item_path)
            except EnvironmentError as edata:
                self.stderr.write(_("Error: processing directory {} failed: {}\n").format(abs_item_path, edata.strerror))
        with repo.open_repo_mgr(self.repo_mgmt_key, writeable=True) as repo_mgr:
            start_counts = repo_mgr.get_counts()
            for abs_item_path in abs_file_link_target_paths:
                abs_dir_path, file_name = os.path.split(abs_item_path)
                try:
                    subdir_ss = self._snapshot.find_or_add_subdir(abs_dir_path)
                    # _include_file() checks that file isn't already included
                    self._include_file(subdir_ss, file_name, abs_item_path, repo_mgr)
                except EnvironmentError as edata:
                    self.stderr.write(_("Error: processing file {} failed: {}\n").format(abs_item_path, edata.strerror))
            self._adjust_item_stats(start_counts, repo_mgr.get_counts())
        self.elapsed_time = bmark.get_os_times() - start_time
    def write_snapshot(self, compress=False, permissions=stat.S_IRUSR|stat.S_IRGRP):
        assert self._snapshot is not None
        import time
        if self._use_gmt:
            snapshot_file_name = time.strftime(_SNAPSHOT_FILE_NAME_TEMPLATE, time.gmtime())
        else:
            snapshot_file_name = time.strftime(_SNAPSHOT_FILE_NAME_TEMPLATE, time.localtime())
        snapshot_file_path = os.path.join(self._archive.snapshot_dir_path, snapshot_file_name)
        if compress is None:
            compress = self._archive.compress_default
        if compress:
            import gzip as io_module
            snapshot_file_path += ".gz"
        else:
            io_module = io
        with io_module.open(snapshot_file_path, "wb") as fobj:
            pickle.dump(SnapshotPlus(self._snapshot, self.creation_stats), fobj, PICKLE_PROTOCOL)
        self._snapshot = None # for refernce count purposes we don't care if the permissions get set
        os.chmod(snapshot_file_path, permissions)
        return (ss_root(snapshot_file_name), os.path.getsize(snapshot_file_path))

GSS = collections.namedtuple("GSS", ["name", "size", "stats", "write_etd"])

def generate_snapshot(archive, compress=None, stderr=sys.stderr, report_skipped_links=True):
    from . import bmark
    with SnapshotGenerator(archive, stderr=stderr, report_skipped_links=report_skipped_links) as snapshot_generator:
        snapshot_generator.generate_snapshot()
        start_time = bmark.get_os_times()
        snapshot_name, snapshot_size = snapshot_generator.write_snapshot(compress=compress)
        elapsed_time = bmark.get_os_times() - start_time
        return GSS(snapshot_name, snapshot_size, snapshot_generator.creation_stats, elapsed_time.get_etd())

class SSFSStats(collections.namedtuple("SSFSStats", ["file_count", "soft_link_count", "content_bytes", "n_citems", "stored_bytes", "stored_bytes_share"])):
    def __add__(self, other):
        return SSFSStats(*[self[i] + other[i] for i in range(len(self))])

class CCStats(collections.namedtuple("CCStats", ["dir_count", "file_count", "soft_link_count", "hard_link_count", "gross_bytes", "net_bytes"])):
    def __add__(self, other):
        return SSFSStats(*[self[i] + other[i] for i in range(len(self))])

class SnapshotFS(collections.namedtuple("SnapshotFS", ["path", "archive_name", "snapshot_name", "snapshot", "repo_mgmt_key"]), PathComponentsMixin):
    @property
    def attributes(self):
        return self.snapshot.attributes
    @property
    def name(self):
        return os.path.basename(self.path)
    def get_file(self, file_path):
        abs_file_path = absolute_path(file_path)
        try:
            file_data = self.snapshot.find_file(abs_file_path, self.repo_mgmt_key)
        except (KeyError, AttributeError):
            try:
                file_link_data = self.snapshot.find_file_link(file_path)
                raise excpns.IsSymbolicLink(file_path, file_link_data.tgt_path)
            except (KeyError, AttributeError):
                pass
            raise excpns.FileNotFound(file_path, self.archive_name, ss_root(self.snapshot_name))
        return file_data
    def get_subdir(self, subdir_path):
        if subdir_path == os.sep:
            return self
        abs_subdir_path = absolute_path(subdir_path)
        subdir_ss = self.snapshot.find_dir(abs_subdir_path)
        if not subdir_ss:
            try:
                subdir_link_data = self.snapshot.find_subdir_link(subdir_path)
                raise excpns.IsSymbolicLink(subdir_path, subdir_link_data.tgt_path)
            except (KeyError, AttributeError):
                pass
            raise excpns.DirNotFound(subdir_path, self.archive_name, ss_root(self.snapshot_name))
        return SnapshotFS(subdir_path, self.archive_name, self.snapshot_name, subdir_ss, self.repo_mgmt_key)
    def iterate_subdirs(self, pre_path=False, recurse=False):
        pre_path = self.path if pre_path is True else "" if pre_path is False else pre_path
        for subdir_name, ss_snapshot in self.snapshot.subdirs.items():
            snapshot_fs = SnapshotFS(os.path.join(pre_path, subdir_name), self.archive_name, self.snapshot_name, ss_snapshot, self.repo_mgmt_key)
            yield snapshot_fs
            if recurse:
                for r_snapshot_fs in snapshot_fs.iterate_subdirs(pre_path=True, recurse=True):
                    yield r_snapshot_fs
    def iterate_files(self, pre_path=False, recurse=False):
        pre_path = self.path if pre_path is True else "" if pre_path is False else pre_path
        for file_name, data in self.snapshot.files.items():
            yield SFile.make(os.path.join(pre_path, file_name), data, self.repo_mgmt_key)
        if recurse:
            for subdir in self.iterate_subdirs():
                for sfile in subdir.iterate_files(pre_path=os.path.join(pre_path, subdir.name), recurse=recurse):
                    yield sfile
    def iterate_subdir_links(self, pre_path=False, recurse=False):
        pre_path = self.path if pre_path is True else "" if pre_path is False else pre_path
        for link_name, data in self.snapshot.subdir_links.items():
            yield SLink.make(os.path.join(pre_path, link_name), data)
        if recurse:
            for subdir in self.iterate_subdirs():
                for slink in subdir.iterate_subdir_links(pre_path=os.path.join(pre_path, subdir.name), recurse=recurse):
                    yield slink
    def iterate_file_links(self, pre_path=False, recurse=False):
        pre_path = self.path if pre_path is True else "" if pre_path is False else pre_path
        for link_name, data in self.snapshot.file_links.items():
            yield SLink.make(os.path.join(pre_path, link_name), data)
        if recurse:
            for subdir in self.iterate_subdirs():
                for slink in subdir.iterate_file_links(pre_path=os.path.join(pre_path, subdir.name), recurse=recurse):
                    yield slink
    def copy_contents_to(self, target_dir_path, overwrite=False, stderr=sys.stderr):
        from . import repo
        # Create the target directory if necessary
        create_dir = True
        dir_count = 0
        if os.path.exists(target_dir_path):
            if os.path.isdir(target_dir_path):
                create_dir = False
                if not overwrite:
                    ow_items = [f for f in self.iterate_files(target_dir_path, True) if os.path.exists(f.path)]
                    ow_items += [f for f in self.iterate_file_links(target_dir_path, True) if os.path.exists(f.path)]
                    ow_items += [f for f in self.iterate_subdir_links(target_dir_path, True) if os.path.exists(f.path)]
                    if ow_items:
                        raise excpns.SubdirOverwriteError(target_dir_path, len(ow_items))
            elif overwrite:
                # remove the file to make way for the directory
                os.remove(target_dir_path)
            else:
                raise excpns.FileOverwriteError(target_dir_path)
        if create_dir:
            os.mkdir(target_dir_path, self.attributes.st_mode)
            os.lchown(target_dir_path, self.attributes.st_uid, self.attributes.st_gid)
            dir_count += 1
        # Now create the subdirs
        for subdir in self.iterate_subdirs(target_dir_path, True):
            try:
                if os.path.isdir(subdir.path):
                    continue
                elif os.path.exists(subdir.path):
                    os.remove(subdir.path)
                os.mkdir(subdir.path, subdir.attributes.st_mode)
                dir_count += 1
                os.lchown(subdir.path, subdir.attributes.st_uid, subdir.attributes.st_gid)
                dir_count += 1
            except EnvironmentError as edata:
                # report the error and move on (we have permission to wreak havoc)
                stderr.write(_("Error: {}: {}\n").format(edata.strerror, edata.filename))
        # and subdir links
        orig_curdir = os.getcwd()
        link_count = 0
        for subdir_link_data in self.iterate_subdir_links(target_dir_path, True):
            link_count += subdir_link_data.create_link(orig_curdir, stderr)
        # Now copy the files
        hard_links = dict()
        file_count = 0
        gross_size = 0
        net_size = 0
        with repo.open_repo_mgr(self.repo_mgmt_key, writeable=False) as repo_mgr:
            for file_data in self.iterate_files(target_dir_path, True):
                if file_data.is_hard_linked:
                    if file_data.attributes.st_ino in hard_links:
                        try:
                            os.link(hard_links[file_data.attributes.st_ino].path, file_data.path)
                            file_count += 1
                            gross_size += file_data.attributes.st_size
                        except EnvironmentError as edata:
                            # report the error and move on (we have permission to wreak havoc)
                            stderr.write(_("Error: hard linking \"{}\" to \"{}\": {}\n").format(file_data.path, hard_links[file_data.attributes.st_ino].path, edata.strerror))
                        continue
                    else:
                        hard_links[file_data.attributes.st_ino] = file_data
                try:
                    repo_mgr.copy_contents_to(file_data.content_token, file_data.path, file_data.attributes)
                except excpns.CopyFileFailed as edata:
                    stderr.write(str(edata) + "\n")
                    continue
                except excpns.SetAttributesFailed as edata:
                    stderr.write(str(edata) + "\n")
                file_count += 1
                gross_size += file_data.attributes.st_size
                net_size += file_data.attributes.st_size
        # and then make the soft links to files
        for file_link_data in self.iterate_file_links(target_dir_path, True):
            link_count += file_link_data.create_link(orig_curdir, stderr)
        return CCStats(dir_count, file_count, link_count, len(hard_links), gross_size, net_size)
    def get_statistics(self):
        from . import repo
        ck_set = set()
        n_files = 0
        n_bytes = 0
        n_stored_bytes = 0
        n_share_bytes = 0
        # NB not using SFile.get_content_storage_stats() for LOCKING efficiency reasons
        with repo.open_repo_mgr(self.repo_mgmt_key, writeable=False) as repo_mgr:
            for file_data in self.iterate_files(recurse=True):
                n_files += 1
                n_bytes += file_data.attributes.st_size
                cis = repo_mgr.get_content_storage_stats(file_data.content_token)
                n_share_bytes += cis.stored_size_per_ref
                if not file_data.content_token in ck_set:
                    n_stored_bytes += cis.stored_size
                    ck_set.add(file_data.content_token)
        n_links = 0
        for link_data in self.iterate_file_links(recurse=True):
            n_links += 1
        for link_data in self.iterate_subdir_links(recurse=True):
            n_links += 1
        return SSFSStats(n_files, n_links, n_bytes, len(ck_set), n_stored_bytes, n_share_bytes)

def get_snapshot_fs(archive_name, seln_fn=lambda l: l[-1]):
    from . import config
    from . import repo
    archive = config.read_archive_spec(archive_name)
    snapshot_names = _get_snapshot_file_list(archive.snapshot_dir_path)
    if not snapshot_names:
        raise excpns.EmptyArchive(archive_name)
    try:
        snapshot_name = seln_fn(snapshot_names)
    except:
        raise excpns.NoMatchingSnapshot([ss_root(ss_name) for ss_name in snapshot_names])
    snapshot = read_snapshot(os.path.join(archive.snapshot_dir_path, snapshot_name))
    repo_mgmt_key = repo.get_repo_mgmt_key(archive.repo_name)
    return SnapshotFS(os.sep, archive_name, ss_root(snapshot_name), snapshot, repo_mgmt_key)

def iter_snapshot_fs_list(archive_name, reverse=False):
    from . import config
    from . import repo
    archive = config.read_archive_spec(archive_name)
    snapshot_names = _get_snapshot_file_list(archive.snapshot_dir_path, reverse=reverse)
    if not snapshot_names:
        raise excpns.EmptyArchive(archive_name)
    repo_mgmt_key = repo.get_repo_mgmt_key(archive.repo_name)
    for snapshot_name in snapshot_names:
        snapshot_file_path = os.path.join(archive.snapshot_dir_path, snapshot_name)
        snapshot = read_snapshot(snapshot_file_path)
        snapshot_fs = SnapshotFS(os.sep, archive_name, ss_root(snapshot_name), snapshot, repo_mgmt_key)
        yield (snapshot_fs, os.path.getsize(snapshot_file_path))

def delete_snapshot(archive_name, seln_fn=lambda l: l[-1], clear_fell=False):
    from . import config
    from . import repo
    archive = config.read_archive_spec(archive_name)
    snapshot_names = _get_snapshot_file_list(archive.snapshot_dir_path)
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
    repo_mgmt_key = repo.get_repo_mgmt_key(archive.repo_name)
    with repo.open_repo_mgr(repo_mgmt_key, writeable=True) as repo_mgr:
        os.remove(snapshot_file_path)
        repo_mgr.release_contents(snapshot.iterate_content_tokens())

def iter_snapshot_list(archive_name, reverse=False):
    from . import config
    archive = config.read_archive_spec(archive_name)
    ss_list = []
    for snapshot_name in _get_snapshot_file_list(archive.snapshot_dir_path, reverse=reverse):
        snapshot_file_path = os.path.join(archive.snapshot_dir_path, snapshot_name)
        snapshot_size = os.path.getsize(snapshot_file_path)
        snapshot_stats = read_snapshot(snapshot_file_path).creation_stats
        yield (ss_root(snapshot_name), snapshot_size, snapshot_stats)

def get_snapshot_name_list(archive_name, reverse=False):
    from . import config
    archive = config.read_archive_spec(archive_name)
    return [(ss_root(f), f.endswith(".gz")) for f in _get_snapshot_file_list(archive.snapshot_dir_path, reverse=reverse)]

def create_new_archive(archive_name, location_dir_path, repo_spec, includes, exclude_dir_globs=None, exclude_file_globs=None, skip_broken_sl=True, compress_default=True):
    from . import config
    base_dir_path = config.write_archive_spec(
        archive_name=archive_name,
        location_dir_path=location_dir_path,
        repo_name=repo_spec.name,
        includes=includes,
        exclude_dir_globs=exclude_dir_globs if exclude_dir_globs else [],
        exclude_file_globs=exclude_file_globs if exclude_file_globs else [],
        skip_broken_sl=skip_broken_sl,
        compress_default=compress_default
    )
    try:
        os.makedirs(base_dir_path)
    except EnvironmentError as edata:
        config.delete_archive_spec(archive_name)
        if edata.errno == errno.EEXIST:
            raise excpns.SnapshotArchiveLocationExists(archive_name)
        elif edata.errno == errno.EPERM or edata.errno == errno.EACCES:
            raise excpns.SnapshotArchiveLocationNoPerm(archive_name)
        else:
            raise edata

def copy_file_to(archive_name, file_path, into_dir_path, seln_fn=lambda l: l[-1], as_name=None, overwrite=False):
    start_times = bmark.get_os_times()
    snapshot_fs = get_snapshot_fs(archive_name, seln_fn)
    file_data = snapshot_fs.get_file(absolute_path(file_path))
    if as_name:
        if os.path.dirname(as_name):
            raise excpns.InvalidArgument(as_name)
        target_path = os.path.join(absolute_path(into_dir_path), as_name)
    else:
        target_path = os.path.join(absolute_path(into_dir_path), os.path.basename(file_path))
    file_data.copy_contents_to(target_path, overwrite=overwrite)
    return (file_data.attributes.st_size, (bmark.get_os_times() - start_times).get_etd())

def copy_subdir_to(archive_name, subdir_path, into_dir_path, seln_fn=lambda l: l[-1], as_name=None, overwrite=False, stderr=sys.stderr):
    start_times = bmark.get_os_times()
    snapshot_fs = get_snapshot_fs(archive_name, seln_fn).get_subdir(absolute_path(subdir_path))
    if as_name:
        if os.path.dirname(as_name):
            raise excpns.InvalidArgument(as_name)
        target_path = os.path.join(absolute_path(into_dir_path), as_name)
    else:
        target_path = os.path.join(absolute_path(into_dir_path), os.path.basename(subdir_path.rstrip(os.sep)))
    copy_stats = snapshot_fs.copy_contents_to(target_path, overwrite=overwrite, stderr=stderr)
    return (copy_stats, (bmark.get_os_times() - start_times).get_etd())

def restore_file(archive_name, file_path, seln_fn=lambda l: l[-1]):
    start_times = bmark.get_os_times()
    abs_file_path = absolute_path(file_path)
    file_data = get_snapshot_fs(archive_name, seln_fn).get_file(abs_file_path)
    file_data.copy_contents_to(abs_file_path, overwrite=True)
    return (file_data.attributes.st_size, (bmark.get_os_times() - start_times).get_etd())

def restore_subdir(archive_name, subdir_path, seln_fn=lambda l: l[-1], stderr=sys.stderr):
    start_times = bmark.get_os_times()
    abs_subdir_path = absolute_path(subdir_path)
    snapshot_fs = get_snapshot_fs(archive_name, seln_fn).get_subdir(abs_subdir_path)
    copy_stats = snapshot_fs.copy_contents_to(abs_subdir_path, overwrite=True, stderr=stderr)
    return (copy_stats, (bmark.get_os_times() - start_times).get_etd())

def get_snapshot_file_path(archive_name, seln_fn=lambda l: l[-1]):
    from . import config
    archive = config.read_archive_spec(archive_name)
    snapshot_names = _get_snapshot_file_list(archive.snapshot_dir_path)
    if not snapshot_names:
        raise excpns.EmptyArchive(archive_name)
    try:
        snapshot_name = seln_fn(snapshot_names)
    except:
        raise excpns.NoMatchingSnapshot([ss_root(ss_name) for ss_name in snapshot_names])
    return os.path.join(archive.snapshot_dir_path, snapshot_name)

def compress_snapshot(archive_name, seln_fn=lambda l: l[-1]):
    snapshot_file_path = get_snapshot_file_path(archive_name, seln_fn)
    if snapshot_file_path.endswith(".gz"):
        raise excpns.SnapshotAlreadyCompressed(archive_name, ss_root(snapshot_file_path))
    utils.compress_file(snapshot_file_path)

def uncompress_snapshot(archive_name, seln_fn=lambda l: l[-1]):
    snapshot_file_path = get_snapshot_file_path(archive_name, seln_fn)
    if not snapshot_file_path.endswith(".gz"):
        raise excpns.SnapshotNotCompressed(archive_name, ss_root(snapshot_file_path))
    utils.uncompress_file(snapshot_file_path)

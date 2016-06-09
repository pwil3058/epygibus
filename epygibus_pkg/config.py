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
import sys
import collections
import fnmatch
import errno
import re

from . import APP_NAME
from . import excpns

APP_NAME_D = APP_NAME + ".d"

_CONFIG_DIR_PATH = os.path.expanduser(os.path.join("~", ".config", APP_NAME_D))
_REPOS_DIR_PATH = os.path.join(_CONFIG_DIR_PATH, "repos")
_ARCHIVES_DIR_PATH = os.path.join(_CONFIG_DIR_PATH, "archives")

if not os.path.exists(_CONFIG_DIR_PATH):
    os.makedirs(_CONFIG_DIR_PATH)
    os.mkdir(_REPOS_DIR_PATH)
    os.mkdir(_ARCHIVES_DIR_PATH)

_repo_file_path = lambda rname: os.path.join(_REPOS_DIR_PATH, rname)
_repo_config_lines = lambda rname: [l.rstrip() for l in open(_repo_file_path(rname), "r").readlines()]

_archive_dir_path = lambda pname: os.path.join(_ARCHIVES_DIR_PATH, pname)
_archive_config_path = lambda pname: os.path.join(_archive_dir_path(pname), "config")
_archive_includes_path = lambda pname: os.path.join(_archive_dir_path(pname), "includes")
_archive_exclude_dirs_path = lambda pname: os.path.join(_archive_dir_path(pname), "exclude_dirs")
_archive_exclude_files_path = lambda pname: os.path.join(_archive_dir_path(pname), "exclude_files")

_archive_config_lines = lambda pname: open(_archive_config_path(pname), "r").readlines()
_includes_file_lines = lambda pname: open(_archive_includes_path(pname), "r").readlines()
_exclude_dir_lines = lambda pname: open(_archive_exclude_dirs_path(pname), "r").readlines()
_exclude_file_lines = lambda pname: open(_archive_exclude_files_path(pname), "r").readlines()

Archive = collections.namedtuple("Archive", ["name", "repo_name", "snapshot_dir_path", "includes", "exclude_dir_globs", "exclude_file_globs", "exclude_dir_cres", "exclude_file_cres", "skip_broken_soft_links", "compress_default"])

def read_archive_spec(archive_name, stderr=sys.stderr):
    try:
        compress_default = "True"
        repo, p_dir_path, skip, compress_default = [l.rstrip() for l in _archive_config_lines(archive_name)]
        includes = [os.path.abspath(os.path.expanduser(f.rstrip())) for f in _includes_file_lines(archive_name)]
        dir_excludes_globs = [glob.rstrip() for glob in _exclude_dir_lines(archive_name)]
        file_excludes_globs = [glob.rstrip() for glob in _exclude_file_lines(archive_name)]
        dir_excludes_cres = [re.compile(fnmatch.translate(os.path.expanduser(glob))) for glob in dir_excludes_globs]
        file_excludes_cres = [re.compile(fnmatch.translate(os.path.expanduser(glob))) for glob in file_excludes_globs]
    except IOError as edata:
        if edata.errno == errno.ENOENT:
            raise excpns.UnknownSnapshotArchive(archive_name)
        else:
            raise edata
    return Archive(archive_name, repo, p_dir_path, includes, dir_excludes_globs, file_excludes_globs, dir_excludes_cres, file_excludes_cres, eval(skip), eval(compress_default))

def write_archive_spec(archive_name, location_dir_path, repo_name, includes, exclude_dir_globs, exclude_file_globs, skip_broken_sl=True, compress_default=True):
    base_dir_path = os.path.join(os.path.abspath(location_dir_path), APP_NAME_D, "snapshots", os.environ["HOSTNAME"], os.environ["USER"], archive_name)
    try:
        os.mkdir(_archive_dir_path(archive_name))
        open(_archive_config_path(archive_name), "w").writelines([p + os.linesep for p in [repo_name, base_dir_path, str(skip_broken_sl), str(compress_default)]])
        open(_archive_includes_path(archive_name), "w").writelines([i + os.linesep for i in includes])
        open(_archive_exclude_dirs_path(archive_name), "w").writelines([x + os.linesep for x in exclude_dir_globs])
        open(_archive_exclude_files_path(archive_name), "w").writelines([x + os.linesep for x in exclude_file_globs])
    except OSError as edata:
        if edata.errno == errno.EEXIST:
            raise excpns.SnapshotArchiveExists(archive_name)
        else:
            raise edata
    return base_dir_path

def delete_archive_spec(archive_name):
    try:
        os.remove(_archive_config_path(archive_name))
        os.remove(_archive_includes_path(archive_name))
        os.remove(_archive_exclude_dirs_path(archive_name))
        os.remove(_archive_exclude_files_path(archive_name))
        os.rmdir(_archive_dir_path(archive_name))
    except IOError as edata:
        if edata.errno == errno.ENOENT:
            raise excpns.UnknownSnapshotArchive(archive_name)
        else:
            raise edata

Repo = collections.namedtuple("Repo", ["name", "base_dir_path", "compressed"])

def read_repo_spec(repo_name):
    from . import excpns
    try:
        base_dir_path, compressed = _repo_config_lines(repo_name)
    except EnvironmentError as edata:
        if edata.errno == errno.ENOENT:
            raise excpns.UnknownBlobRepository(repo_name)
        else:
            raise edata
    return Repo(repo_name, base_dir_path, eval(compressed))

def write_repo_spec(repo_name, in_dir_path, compressed=True):
    base_dir_path = os.path.join(os.path.abspath(in_dir_path), APP_NAME_D, "blobs", os.environ["USER"], repo_name)
    cf_path = _repo_file_path(repo_name)
    if os.path.exists(cf_path):
        raise excpns.BlobRepositoryExists(repo_name)
    open(cf_path, "w").writelines([p + os.linesep for p in [base_dir_path, str(compressed)]])
    return Repo(repo_name, base_dir_path, compressed)

def delete_repo_spec(repo_name):
    try:
        os.remove(_repo_file_path(repo_name))
    except EnvironmentError as edata:
        if edata.errno == errno.ENOENT:
            raise excpns.UnknownBlobRepository(repo_name)
        else:
            raise edata

def get_includes_file_path(archive_name):
    return _archive_includes_path(archive_name)

def get_exclude_dirs_file_path(archive_name):
    return _archive_exclude_dirs_path(archive_name)

def get_exclude_files_file_path(archive_name):
    return _archive_exclude_files_path(archive_name)

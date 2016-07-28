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

_repo_file_path = lambda repo_name: os.path.join(_REPOS_DIR_PATH, repo_name)

def read_repo_config_lines(repo_name):
    with open(_repo_file_path(repo_name), "r") as f_obj:
        return [l.rstrip() for l in f_obj.readlines()]

_archive_dir_path = lambda archive_name: os.path.join(_ARCHIVES_DIR_PATH, archive_name)
_archive_config_path = lambda archive_name: os.path.join(_archive_dir_path(archive_name), "config")
_archive_includes_path = lambda archive_name: os.path.join(_archive_dir_path(archive_name), "includes")
_archive_exclude_dirs_path = lambda archive_name: os.path.join(_archive_dir_path(archive_name), "exclude_dirs")
_archive_exclude_files_path = lambda archive_name: os.path.join(_archive_dir_path(archive_name), "exclude_files")

def read_archive_config_lines(archive_name):
    with open(_archive_config_path(archive_name), "r") as f_obj:
        return [l.rstrip() for l in f_obj.readlines()]

def write_archive_config_lines(archive_name, lines):
    with open(_archive_config_path(archive_name), "w") as f_obj:
        f_obj.writelines([l.rstrip() + os.linesep for l in lines])

def read_includes_file_lines(archive_name):
    with open(_archive_includes_path(archive_name), "r") as f_obj:
        return [l.rstrip() for l in f_obj.readlines()]

def write_includes_file_lines(archive_name, lines):
    with open(_archive_includes_path(archive_name), "w") as f_obj:
        f_obj.writelines([l.rstrip() + os.linesep for l in lines])

def read_exclude_dir_lines(archive_name):
    with open(_archive_exclude_dirs_path(archive_name), "r") as f_obj:
        return [l.rstrip() for l in f_obj.readlines()]

def write_exclude_dir_lines(archive_name, lines):
    with open(_archive_exclude_dirs_path(archive_name), "w") as f_obj:
        f_obj.writelines([l.rstrip() + os.linesep for l in lines])

def read_exclude_file_lines(archive_name):
    with open(_archive_exclude_files_path(archive_name), "r") as f_obj:
        return [l.rstrip() for l in f_obj.readlines()]

def write_exclude_file_lines(archive_name, lines):
    with open(_archive_exclude_files_path(archive_name), "w") as f_obj:
        f_obj.writelines([l.rstrip() + os.linesep for l in lines])

Archive = collections.namedtuple("Archive", ["name", "repo_name", "snapshot_dir_path", "includes", "exclude_dir_globs", "exclude_file_globs", "skip_broken_soft_links", "compress_default"])

def read_archive_spec(archive_name, stderr=sys.stderr):
    try:
        repo, p_dir_path, skip, compress_default = read_archive_config_lines(archive_name)
        # NB: leave expansion to absolute paths to the snapshot generator
        includes = read_includes_file_lines(archive_name)
        dir_excludes_globs = read_exclude_dir_lines(archive_name)
        file_excludes_globs = read_exclude_file_lines(archive_name)
    except FileNotFoundError:
        raise excpns.UnknownSnapshotArchive(archive_name)
    return Archive(archive_name, repo, p_dir_path, includes, dir_excludes_globs, file_excludes_globs, eval(skip), eval(compress_default))

def write_archive_spec(archive_name, location_dir_path, repo_name, includes, exclude_dir_globs, exclude_file_globs, skip_broken_sl=True, compress_default=True):
    base_dir_path = os.path.join(os.path.abspath(location_dir_path), APP_NAME_D, "snapshots", os.environ["HOSTNAME"], os.environ["USER"], archive_name)
    try:
        os.mkdir(_archive_dir_path(archive_name))
        write_archive_config_lines(archive_name, [repo_name, base_dir_path, str(skip_broken_sl), str(compress_default)])
        write_includes_file_lines(archive_name, includes)
        write_exclude_dir_lines(archive_name, exclude_dir_globs)
        write_exclude_file_lines(archive_name, exclude_file_globs)
    except FileExistsError:
        raise excpns.SnapshotArchiveExists(archive_name)
    return base_dir_path

def delete_archive_spec(archive_name):
    try:
        os.remove(_archive_config_path(archive_name))
        os.remove(_archive_includes_path(archive_name))
        os.remove(_archive_exclude_dirs_path(archive_name))
        os.remove(_archive_exclude_files_path(archive_name))
        os.rmdir(_archive_dir_path(archive_name))
    except FileNotFoundError:
        raise excpns.UnknownSnapshotArchive(archive_name)

Repo = collections.namedtuple("Repo", ["name", "base_dir_path", "compressed"])

def read_repo_spec(repo_name):
    from . import excpns
    try:
        base_dir_path, compressed = read_repo_config_lines(repo_name)
    except FileNotFoundError:
        raise excpns.UnknownRepository(repo_name)
    return Repo(repo_name, base_dir_path, eval(compressed))

def write_repo_spec(repo_name, in_dir_path, compressed=True):
    base_dir_path = os.path.join(os.path.abspath(in_dir_path), APP_NAME_D, "repos", os.environ["USER"], repo_name)
    cf_path = _repo_file_path(repo_name)
    if os.path.exists(cf_path):
        raise excpns.RepositoryExists(repo_name)
    with open(cf_path, "w") as f_obj:
        f_obj.writelines([p + os.linesep for p in [base_dir_path, str(compressed)]])
    return Repo(repo_name, base_dir_path, compressed)

def delete_repo_spec(repo_name):
    try:
        os.remove(_repo_file_path(repo_name))
    except FileNotFoundError:
        raise excpns.UnknownRepository(repo_name)

def get_includes_file_path(archive_name):
    return _archive_includes_path(archive_name)

def get_exclude_dirs_file_path(archive_name):
    return _archive_exclude_dirs_path(archive_name)

def get_exclude_files_file_path(archive_name):
    return _archive_exclude_files_path(archive_name)

def get_archive_name_list():
    return [name for name in os.listdir(_ARCHIVES_DIR_PATH) if os.path.isdir(os.path.join(_ARCHIVES_DIR_PATH, name))]

def get_repo_name_list():
    return [name for name in os.listdir(_REPOS_DIR_PATH) if os.path.isfile(os.path.join(_REPOS_DIR_PATH, name))]

def get_repo_spec_list():
    return [read_repo_spec(name) for name in get_repo_name_list()]

def get_archive_spec_list():
    return [read_archive_spec(name) for name in get_archive_name_list()]

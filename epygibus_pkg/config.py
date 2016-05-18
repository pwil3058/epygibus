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

from . import APP_NAME

APP_NAME_D = APP_NAME + ".d"

class Error(Exception):
    def __init__(self, *args, **kargs):
        self.args = args
        self.kargs = kargs

class ErrorRepoSpecExists(Error):
    pass

_CONFIG_DIR_PATH = os.path.expanduser(os.path.join("~", ".config", APP_NAME_D))
_REPOS_DIR_PATH = os.path.join(_CONFIG_DIR_PATH, "repos")
_PROFILES_DIR_PATH = os.path.join(_CONFIG_DIR_PATH, "profiles")

if not os.path.exists(_CONFIG_DIR_PATH):
    os.makedirs(_CONFIG_DIR_PATH)
    os.mkdir(_REPOS_DIR_PATH)
    os.mkdir(_PROFILES_DIR_PATH)

_repo_file_path = lambda rname: os.path.join(_REPOS_DIR_PATH, rname)

_profile_dir_path = lambda pname: os.path.join(_PROFILES_DIR_PATH, pname)
_profile_config_path = lambda pname: os.path.join(_profile_dir_path(pname), "config")
_profile_includes_path = lambda pname: os.path.join(_profile_dir_path(pname), "includes")
_profile_exclude_dirs_path = lambda pname: os.path.join(_profile_dir_path(pname), "exclude_dirs")
_profile_exclude_files_path = lambda pname: os.path.join(_profile_dir_path(pname), "exclude_files")

_profile_config_lines = lambda pname: open(_profile_config_path(pname), "r").readlines()
_includes_file_lines = lambda pname: open(_profile_includes_path(pname), "r").readlines()
_exclude_dir_lines = lambda pname: open(_profile_exclude_dirs_path(pname), "r").readlines()
_exclude_file_lines = lambda pname: open(_profile_exclude_files_path(pname), "r").readlines()

Profile = collections.namedtuple("Profile", ["repo_name", "snapshot_dir_path", "includes", "exclude_dir_cres", "exclude_file_cres", "skip_broken_soft_links"])

def read_profile_spec(profile_name, stderr=sys.stderr):
    repo, p_dir_path, skip = [l.rstrip() for l in _profile_config_lines(profile_name)]
    includes = [os.path.abspath(os.path.expanduser(f.rstrip())) for f in _includes_file_lines(profile_name)]
    dir_excludes = [fnmatch.translate(os.path.expanduser(glob.rstrip())) for glob in _exclude_dir_lines(profile_name)]
    file_excludes = [fnmatch.translate(os.path.expanduser(glob.rstrip())) for glob in _exclude_file_lines(profile_name)]
    return Profile(repo, p_dir_path, includes, dir_excludes, file_excludes, eval(skip))

def write_profile_spec(profile_name, in_dir_path, repo_name, includes, exclude_dirs, exclude_files, skip_broken_sl=True):
    base_dir_path = os.path.join(os.path.abspath(in_dir_path), APP_NAME_D, "snapshots", os.environ["HOSTNAME"], os.environ["USER"], profile_name)
    os.mkdir(_profile_dir_path(profile_name))
    open(_profile_config_path(profile_name), "w").writelines([p + os.linesep for p in[repo_name, base_dir_path, str(skip_broken_sl)]])
    open(_profile_includes_path(profile_name), "w").writelines(includes)
    open(_profile_exclude_dirs_path(profile_name), "w").writelines(exclude_dirs)
    open(_profile_exclude_files_path(profile_name), "w").writelines(exclude_files)
    return base_dir_path

def delete_profile_spec(profile_name):
    os.remove(_profile_config_path(profile_name))
    os.remove(_profile_includes_path(profile_name))
    os.remove(_profile_exclude_dirs_path(profile_name))
    os.remove(_profile_exclude_files_path(profile_name))
    os.rmdir(_profile_dir_path(profile_name))

Repo = collections.namedtuple("Repo", ["base_dir_path"])

def read_repo_spec(repo_name):
    base_dir_path = open(_repo_file_path(repo_name)).read().rstrip()
    return Repo(base_dir_path)

def write_repo_spec(repo_name, in_dir_path):
    base_dir_path = os.path.join(os.path.abspath(in_dir_path), APP_NAME_D, "blobs", repo_name)
    cf_path = _repo_file_path(repo_name)
    if os.path.exists(cf_path):
        raise ErrorRepoSpecExists(name=repo_name)
    open(cf_path, "w").write(base_dir_path)
    return base_dir_path

def delete_repo_spec(repo_name):
    os.remove(_repo_file_path(repo_name))

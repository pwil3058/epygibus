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

_CONFIG_DIR_PATH = os.path.expanduser(os.path.join("~", ".config", APP_NAME + ".d"))
_REPOS_DIR_PATH = os.path.join(_CONFIG_DIR_PATH, "repos")
_PROFILES_DIR_PATH = os.path.join(_CONFIG_DIR_PATH, "profiles")

if not os.path.exists(_CONFIG_DIR_PATH):
    os.makedirs(_CONFIG_DIR_PATH)
    os.mkdir(_REPOS_DIR_PATH)
    os.mkdir(_PROFILES_DIR_PATH)

_profiles_config_lines = lambda pname: open(os.path.join(_PROFILES_DIR_PATH, pname, "config"), "r").readlines()
_includes_file_lines = lambda pname: open(os.path.join(_PROFILES_DIR_PATH, pname, "includes"), "r").readlines()
_exclude_dir_lines = lambda pname: open(os.path.join(_PROFILES_DIR_PATH, pname, "exclude_dirs"), "r").readlines()
_exclude_file_lines = lambda pname: open(os.path.join(_PROFILES_DIR_PATH, pname, "exclude_files"), "r").readlines()

Profile = collections.namedtuple("Profile", ["repo_name", "snapshot_dir_path", "includes", "exclude_dir_cres", "exclude_file_cres", "skip_broken_soft_links"])

def read_profile_spec(profile_name, stderr=sys.stderr):
    repo, p_dir_path, skip = [l.rstrip() for l in _profiles_config_lines(profile_name)]
    includes = [os.path.abspath(os.path.expanduser(f.rstrip())) for f in _includes_file_lines(profile_name)]
    dir_excludes = [fnmatch.translate(os.path.expanduser(glob.rstrip())) for glob in _exclude_dir_lines(profile_name)]
    file_excludes = [fnmatch.translate(os.path.expanduser(glob.rstrip())) for glob in _exclude_file_lines(profile_name)]
    return Profile(repo, p_dir_path, includes, dir_excludes, file_excludes, eval(skip))

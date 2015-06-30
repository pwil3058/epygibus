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

class Profile(object):
    repo_name = None
    snapshot_dir_path = "test"
    includes = ["~/Downloads", "~/Dropbox/bedienung_infinity_2009.pdf"]
    exclude_dir_cres = list()
    exclude_file_cres = list()
    skip_broken_soft_links = False

def read_profile_spec(profile_name):
    return Profile()

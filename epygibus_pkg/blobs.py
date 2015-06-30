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

class DummyBlobMgr(object):
    @staticmethod
    def store_contents(file_path):
        import hashlib
        return hashlib.sha1(open(file_path, "r").read()).hexdigest()
    @staticmethod
    def release_lock():
        pass

def open_repo(repo_name, locked=False):
    return DummyBlobMgr()

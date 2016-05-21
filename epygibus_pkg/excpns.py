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

class Error(Exception):
    STR_TEMPLATE = "Error:"
    def __str__(self):
        print "STR", self.__dict__
        return self.STR_TEMPLATE.format(**self.__dict__)

class NotFoundInSnapshot(Error):
    STR_TEMPLATE = _("Error: file/directory \"{path}\" not found in \"{archive_name}::{snapshot_name}\" snapshot.")
    def __init__(self, path, archive_name, snapshot_name):
        self.path = path
        self.archive_name = archive_name
        self.snapshot_name = snapshot_name

class UnknownSnapshotArchive(Error):
    STR_TEMPLATE = _("Error: snapshot archive \"{archive_name}\" is not defined.")
    def __init__(self, archive_name):
        self.archive_name = archive_name

class EmptyArchive(Error):
    STR_TEMPLATE = _("Error: snapshot archive \"{archive_name}\" is empty.")
    def __init__(self, archive_name):
        self.archive_name = archive_name

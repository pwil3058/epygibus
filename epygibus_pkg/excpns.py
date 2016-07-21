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
        return self.STR_TEMPLATE.format(**self.__dict__)

class InvalidArgument(Error):
    STR_TEMPLATE = _("Error: invalid argument: \"{argument}\".")
    def __init__(self, argument):
        self.argument = argument

class CopyFileFailed(Error):
    STR_TEMPLATE = _("Error: copying \"{file_path}\" failed: {reason}.")
    def __init__(self, file_path, reason):
        self.file_path = file_path
        self.reason = reason

class SetAttributesFailed(Error):
    STR_TEMPLATE = _("Error: setting \"{file_path}\" attributes failed: {reason}.")
    def __init__(self, file_path, reason):
        self.file_path = file_path
        self.reason = reason

class DirNotFound(Error):
    STR_TEMPLATE = _("Error: directory \"{dir_path}\" not found in \"{archive_name}::{snapshot_name}\" snapshot.")
    def __init__(self, dir_path, archive_name, snapshot_name):
        self.dir_path = dir_path
        self.archive_name = archive_name
        self.snapshot_name = snapshot_name

class FileNotFound(Error):
    STR_TEMPLATE = _("Error: file \"{file_path}\" not found in \"{archive_name}::{snapshot_name}\" snapshot.")
    def __init__(self, file_path, archive_name, snapshot_name):
        self.file_path = file_path
        self.archive_name = archive_name
        self.snapshot_name = snapshot_name

class IsSymbolicLink(Error):
    STR_TEMPLATE = _("Error: path \"{path}\" is a symbolic link to \"{tgt_path}\".")
    def __init__(self, path, tgt_path):
        self.path = path
        self.tgt_path = tgt_path

class FileOverwriteError(Error):
    STR_TEMPLATE = _("Error: file \"{target_file_path}\" already exists. Use --overwrite to overwrite it.")
    def __init__(self, target_file_path):
        self.target_file_path = target_file_path

class SubdirOverwriteError(Error):
    STR_TEMPLATE = _("Error: directory \"{target_dir_path}\" contains {nfiles} file(s) that will be overwritten. Use --overwrite to overwrite them.")
    def __init__(self, target_dir_path, nfiles):
        self.target_dir_path = target_dir_path
        self.nfiles = nfiles

class NotRegularFile(Error):
    STR_TEMPLATE = _("Error: \"{file_name}\" is not a regular file.")
    def __init__(self, file_name):
        self.file_name = file_name

class UnknownSnapshotArchive(Error):
    STR_TEMPLATE = _("Error: snapshot archive \"{archive_name}\" is not defined.")
    def __init__(self, archive_name):
        self.archive_name = archive_name

class SnapshotArchiveExists(Error):
    STR_TEMPLATE = _("Error: snapshot archive \"{archive_name}\" is already defined.")
    def __init__(self, archive_name):
        self.archive_name = archive_name

class SnapshotArchiveLocationExists(Error):
    STR_TEMPLATE = _("Error: location for snapshot archive \"{archive_name}\" already exists.")
    def __init__(self, archive_name):
        self.archive_name = archive_name

class SnapshotArchiveLocationNoPerm(Error):
    STR_TEMPLATE = _("Error: permission denied creating location for snapshot archive \"{archive_name}\".")
    def __init__(self, archive_name):
        self.archive_name = archive_name

class UnknownRepository(Error):
    STR_TEMPLATE = _("Error: content repository \"{repo_name}\" is not defined.")
    def __init__(self, repo_name):
        self.repo_name = repo_name

class RepositoryExists(Error):
    STR_TEMPLATE = _("Error: content repository \"{repo_name}\" is already defined.")
    def __init__(self, repo_name):
        self.repo_name = repo_name

class RepositoryLocationExists(Error):
    STR_TEMPLATE = _("Error: content repository \"{repo_name}\" location already exists.")
    def __init__(self, repo_name):
        self.repo_name = repo_name

class RepositoryLocationNoPerm(Error):
    STR_TEMPLATE = _("Error: content repository \"{repo_name}\" location permission denied.")
    def __init__(self, repo_name):
        self.repo_name = repo_name

class RepositoryInUse(Error):
    STR_TEMPLATE = _("Error: content repository \"{repo_name}\" in use with {num_refed_items} being referenced.")
    def __init__(self, repo_name, num_refed_items):
        self.repo_name = repo_name
        self.num_refed_items = num_refed_items

class EmptyArchive(Error):
    STR_TEMPLATE = _("Error: snapshot archive \"{archive_name}\" is empty.")
    def __init__(self, archive_name):
        self.archive_name = archive_name

class LastSnapshot(Error):
    STR_TEMPLATE = _("Error: snapshot \"{snapshot_name}\" is the last one remaining in \"{archive_name}\" archive.")
    def __init__(self, archive_name, snapshot_name):
        self.archive_name = archive_name
        self.snapshot_name = snapshot_name

class NoMatchingSnapshot(Error):
    STR_TEMPLATE = _("Error: snapshot matching selection criteria not found in {available_snapshots}.")
    def __init__(self, available_snapshots):
        self.available_snapshots = available_snapshots

class SnapshotNotFound(Error):
    STR_TEMPLATE = _("Error: snapshot \"{snapshot_name}\" not found in {archive_name} archive.")
    def __init__(self, archive_name, snapshot_name):
        self.archive_name = archive_name
        self.archive_name = snapshot_name

class SnapshotAlreadyCompressed(Error):
    STR_TEMPLATE = _("Error: snapshot \"{snapshot_name}\" in \"{archive_name}\" already compressed.")
    def __init__(self, archive_name, snapshot_name):
        self.archive_name = archive_name
        self.snapshot_name = snapshot_name

class SnapshotNotCompressed(Error):
    STR_TEMPLATE = _("Error: snapshot \"{snapshot_name}\" in \"{archive_name}\" is not compressed.")
    def __init__(self, archive_name, snapshot_name):
        self.archive_name = archive_name
        self.snapshot_name = snapshot_name

class InvalidSnapshotFile(Error):
    STR_TEMPLATE = _("Error: file \"{file_path}\" is not a valid snapshot file.")
    def __init__(self, file_path):
        self.file_path = file_path

### Copyright (C) 2016 Peter Williams <pwil3058@gmail.com>
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

import hashlib
import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject

from . import actions

class ModifyUndoSaveBuffer(Gtk.TextBuffer, actions.CBGUserMixin):
    AC_MODIFIED = actions.ActionCondns.new_flag()
    AC_MODIFIED_ON_DISK = actions.ActionCondns.new_flag()
    def __init__(self):
        Gtk.TextBuffer.__init__(self)
        actions.CBGUserMixin.__init__(self)
        self.connect("changed", self._buffer_changed_cb)
        self.connect("modified-changed", self._buffer_changed_cb)
    def _buffer_changed_cb(self, _buffer=None):
        if self.get_modified():
            self.button_groups.update_condns(actions.MaskedCondns(self.AC_MODIFIED, self.AC_MODIFIED))
        else:
            self.button_groups.update_condns(actions.MaskedCondns(0, self.AC_MODIFIED))

class FileModifyUndoSaveBuffer(ModifyUndoSaveBuffer):
    def __init__(self, file_path=None):
        self._file_path = file_path
        self._hash_digest = None
        ModifyUndoSaveBuffer.__init__(self)
        if file_path:
            self.load_file()
    def load_file(self):
        with open(self._file_path, "r") as f_obj:
            text = f_obj.read()
            self._hash_digest = hashlib.sha1(text).digest()
            self.set_text(text)
    def save_file(self):
        with open(self._file_path, "w") as f_obj:
            for line in self.get_text(self.get_start_iter(), self.get_end_iter(), True).splitlines(False):
                f_obj.write(line.rstrip() + os.linesep)
        self.load_file()
    def get_current_hash_digest(self):
        return hashlib.sha1(self.get_text(self.get_start_iter(), self.get_end_iter(), True)).digest()
    def get_file_hash_digest(self):
        if not self._file_path or not os.path.isfile(file_path):
            return None
        with open(self._file_path, "r") as f_obj:
            return hashlib.sha1(f_obj.read()).digest()
    @property
    def modified_on_disk(self):
        return self.get_file_hash_digest() != self._hash_digest
    def _check_file_cb(self, _data):
        # NB: the view should register this so that its "destroy" signal can be used to deregister it
        if self.modified_on_disk:
            self.button_groups.update_condns(actions.MaskedCondns(self.AC_MODIFIED_ON_DISK, self.AC_MODIFIED_ON_DISK))
        else:
            self.button_groups.update_condns(actions.MaskedCondns(0, self.AC_MODIFIED_ON_DISK))
        return True

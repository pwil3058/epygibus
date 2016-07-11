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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject

from .. import snapshot
from .. import excpns

from . import actions
from . import dialogue
from . import tlview
from . import icons

DVRow = collections.namedtuple("DVRow", ["name", "icon", "is_dir", "is_link"])

class DVModel(tlview.NamedListStore):
    Row = DVRow
    types = DVRow(name=GObject.TYPE_STRING, icon=GObject.TYPE_STRING, is_dir=GObject.TYPE_BOOLEAN, is_link=GObject.TYPE_BOOLEAN)

def dv_specification():
    return tlview.ViewSpec(
        properties={
            "enable-grid-lines" : False,
            "reorderable" : False,
            "rules_hint" : False,
            "headers-visible" : False,
        },
        selection_mode = Gtk.SelectionMode.MULTIPLE,
        columns = [
            tlview.simple_column("", tlview.stock_icon_cell(DVModel, "icon", xalign=0.0)),
            tlview.simple_column(_("Name"), tlview.fixed_text_cell(DVModel, "name", xalign=0.0)),
        ]
    )

class DirectoryView(tlview.ListView, actions.CAGandUIManager, dialogue.BusyIndicatorUser):
    PopUp = None
    Model = DVModel
    specification = dv_specification()
    def __init__(self, snapshot_fs, offset_dir_path, busy_indicator=None, size_req=None):
        tlview.ListView.__init__(self)
        dialogue.BusyIndicatorUser.__init__(self, busy_indicator)
        actions.CAGandUIManager.__init__(self, selection=self.get_selection(), popup=self.PopUp)
        if size_req:
            self.set_size_request(size_req[0], size_req[1])
        self.connect("button_press_event", tlview.clear_selection_cb)
        self.connect("key_press_event", tlview.clear_selection_cb)
        self._snapshot_fs = snapshot_fs
        self._offset_dir_path = offset_dir_path
        self._set_contents()
    def populate_action_groups(self):
        pass
    def _set_contents(self):
        offset_subdir_fs = self._snapshot_fs.get_subdir(self._offset_dir_path)
        real_dirs = [DVRow(key, icons.STOCK_DIR, True, False) for key in offset_subdir_fs.subdirs.keys()]
        dir_links = [DVRow(key, icons.STOCK_DIR_LINK, True, True) for key in offset_subdir_fs.subdir_links.keys()]
        real_files = [DVRow(key, icons.STOCK_FILE, False, False) for key in offset_subdir_fs.files.keys()]
        file_links = [DVRow(key, icons.STOCK_FILE_LINK, False, True) for key in offset_subdir_fs.file_links.keys()]
        self.model.clear()
        for dr in sorted(real_dirs + dir_links):
            self.model.append(dr)
        for fr in sorted(real_files + file_links):
            self.model.append(fr)

class ExigSnapshotDialog(dialogue.AmodalDialog):
    def __init__(self, snapshot_fs, parent=None):
        title = _("Snapshot Exigency: {}:{}").format(snapshot_fs.archive_name, snapshot_fs.snapshot_name)
        dialogue.AmodalDialog.__init__(self, title=title, parent=parent, flags=0, buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        self.connect("response", self._response_cb)
        self._snapshot_fs = snapshot_fs
        self._base_offset_dir_path = snapshot_fs.get_offset_base_subdir_path()
        self._current_offset_dir_path = self._base_offset_dir_path
        self._dir_view = DirectoryView(self._snapshot_fs, self._current_offset_dir_path)
        self.get_content_area().pack_start(self._dir_view, expand=True, fill=True, padding=0)
        self.show_all()
    def _response_cb(self, dialog, response_id):
        self.destroy()

def exig_open_snapshot_file_acb(_action=None):
    snapshot_file_path = dialogue.ask_file_path(_("Snapshot File Path:"))
    if snapshot_file_path:
        try:
            snapshot_fs = snapshot.get_snapshot_fs_fm_file(snapshot_file_path)
        except (excpns.Error, IOError) as edata:
            dialogue.report_exception_as_error(edata)
            return
        ExigSnapshotDialog(snapshot_fs).show()

actions.CLASS_INDEP_AGS[actions.AC_DONT_CARE].add_actions(
    [
        ("snapshot_exigency_menu", None, _("Snapshot Exigencies")),
        ("exig_open_snapshot_file", icons.STOCK_OPEN_SNAPSHOT_FILE, _("Open Snapshot File"), None,
         _("(Exigency) open a snapshot file."),
         exig_open_snapshot_file_acb
        ),
    ])

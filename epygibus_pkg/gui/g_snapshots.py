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
import os

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
from . import gutils

AC_ABOVE_BASE_OFFSET = actions.ActionCondns.new_flag()

DVRow = collections.namedtuple("DVRow", ["name", "icon", "is_dir", "is_link"])

class DVModel(tlview.NamedListStore):
    Row = DVRow
    types = DVRow(name=GObject.TYPE_STRING, icon=GObject.TYPE_STRING, is_dir=GObject.TYPE_BOOLEAN, is_link=GObject.TYPE_BOOLEAN)
    def __init__(self, snapshot_fs=None, offset_dir_path=None):
        tlview.NamedListStore.__init__(self)
        self.set_snapshot_fs(snapshot_fs, offset_dir_path)
    def _set_contents(self):
        if self._snapshot_fs is None:
            self.clear()
            return
        offset_subdir_fs = self._snapshot_fs.get_subdir(self._offset_dir_path)
        real_dirs = [DVRow(key, icons.STOCK_DIR, True, False) for key in offset_subdir_fs.subdirs.keys()]
        dir_links = [DVRow(key, icons.STOCK_DIR_LINK, True, True) for key in offset_subdir_fs.subdir_links.keys()]
        real_files = [DVRow(key, icons.STOCK_FILE, False, False) for key in offset_subdir_fs.files.keys()]
        file_links = [DVRow(key, icons.STOCK_FILE_LINK, False, True) for key in offset_subdir_fs.file_links.keys()]
        self.clear()
        self.append_contents(sorted(real_dirs + dir_links))
        self.append_contents(sorted(real_files + file_links))
    def change_offset_dir_path(self, new_offset_dir_path):
        self._offset_dir_path = new_offset_dir_path
        self._set_contents()
    def set_snapshot_fs(self, snapshot_fs, offset_dir_path=None):
        assert (snapshot_fs and offset_dir_path) or (not snapshot_fs and not offset_dir_path)
        self._snapshot_fs = snapshot_fs
        self._offset_dir_path = offset_dir_path
        self._set_contents()

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

class DirectoryView(tlview.ListView):
    PopUp = None
    Model = DVModel
    specification = dv_specification()
    def __init__(self, snapshot_fs, offset_dir_path, size_req=None):
        self._dv_model = self.Model(snapshot_fs, offset_dir_path)
        self.show_hidden_toggle = Gtk.CheckButton(_("Show Hidden"))
        show_hidden_filter = self._dv_model.filter_new()
        show_hidden_filter.set_visible_func(self._show_hidden_visibility_func, self.show_hidden_toggle)
        self.show_hidden_toggle.connect("toggled", lambda _widget: show_hidden_filter.refilter())
        tlview.ListView.__init__(self, model=show_hidden_filter, size_req=size_req)
        self.connect("button_press_event", tlview.clear_selection_cb)
        self.connect("key_press_event", tlview.clear_selection_cb)
    def _show_hidden_visibility_func(self, model, model_iter, toggle):
        return toggle.get_active() or not model.get_value_named(model_iter, "name").startswith(".")
    def change_offset_dir_path(self, new_offset_dir_path):
        self._dv_model.change_offset_dir_path(new_offset_dir_path)
    def set_snapshot_fs(self, snapshot_fs, offset_dir_path=None):
        self._dv_model.set_snapshot_fs(snapshot_fs, offset_dir_path)

class SnapshotManagerWidget(Gtk.VBox, actions.CAGandUIManager, actions.CBGUserMixin, dialogue.BusyIndicatorUser):
    def __init__(self, snapshot_fs, busy_indicator=None, parent=None):
        Gtk.VBox.__init__(self)
        self._snapshot_fs = snapshot_fs
        self._base_offset_dir_path = snapshot_fs.get_offset_base_subdir_path() if snapshot_fs else None
        self._current_offset_dir_path = self._base_offset_dir_path
        self._dir_view = DirectoryView(self._snapshot_fs, self._current_offset_dir_path)
        actions.CAGandUIManager.__init__(self, self._dir_view.get_selection())
        actions.CBGUserMixin.__init__(self, self._dir_view.get_selection())
        dialogue.BusyIndicatorUser.__init__(self, busy_indicator=busy_indicator)
        up_button = self.button_groups.get_button("snapshot_dir_go_up")
        self._current_dir_path_label = Gtk.Label()
        self._current_dir_path_label.set_xalign(0.0)
        hbox = Gtk.HBox()
        hbox.pack_start(up_button, expand=False, fill=False, padding=0)
        hbox.pack_start(self._current_dir_path_label, expand=True, fill=True, padding=0)
        self.pack_start(hbox, expand=False, fill=True, padding=0)
        self.pack_start(gutils.wrap_in_scrolled_window(self._dir_view), expand=True, fill=True, padding=0)
        bbox = self.button_groups.create_action_button_box(["snapshot_dir_show_hidden"])
        self.pack_start(bbox, expand=False, fill=True, padding=0)
        self._dir_view.connect("row_activated", self._double_click_cb)
        self._update_above_base_offset_status()
        self.show_all()
    def populate_action_groups(self):
        pass
    def populate_button_groups(self):
        self.button_groups[actions.AC_DONT_CARE].add_buttons(
            [
                ("snapshot_dir_show_hidden", self._dir_view.show_hidden_toggle,
                 _("Show/hide hidden files and directories."),
                 self._change_dir_up_bcb),
            ])
        self.button_groups[AC_ABOVE_BASE_OFFSET].add_buttons(
            [
                ("snapshot_dir_go_up", Gtk.Button.new_from_icon_name(Gtk.STOCK_GO_UP, Gtk.IconSize.BUTTON),
                 _("Change displayed directory to parent of current displayed directory."),
                 self._change_dir_up_bcb),
            ])
    def _double_click_cb(self, tree_view, tree_path, tree_view_column):
        model = tree_view.get_model().get_model()
        row = model.get_row(model.get_iter(tree_path))
        if row.is_dir:
            self._current_offset_dir_path = os.path.join(self._current_offset_dir_path, row.name)
            tree_view.change_offset_dir_path(self._current_offset_dir_path)
            self._update_above_base_offset_status()
    def _change_dir_up_bcb(self, _button=None):
        if self._current_offset_dir_path == self._base_offset_dir_path:
            return
        self._current_offset_dir_path = os.path.dirname(self._current_offset_dir_path)
        self._dir_view.change_offset_dir_path(self._current_offset_dir_path)
        self._update_above_base_offset_status()
    def _update_above_base_offset_status(self):
        self._current_dir_path_label.set_text(str(self._current_offset_dir_path))
        if self._current_offset_dir_path == self._base_offset_dir_path:
            condns =actions.MaskedCondns(0, AC_ABOVE_BASE_OFFSET)
        else:
            condns =actions.MaskedCondns(AC_ABOVE_BASE_OFFSET, AC_ABOVE_BASE_OFFSET)
        self.button_groups.update_condns(condns)
        self.action_groups.update_condns(condns)

class ExigSnapshotDialog(Gtk.Window):
    def __init__(self, snapshot_fs, parent=None):
        title = _("Snapshot Exigency: {}:{}").format(snapshot_fs.archive_name, snapshot_fs.snapshot_name)
        Gtk.Window.__init__(self, title=title, type=Gtk.WindowType.TOPLEVEL)
        self._ss_mgr = SnapshotManagerWidget(snapshot_fs, parent=parent)
        self.add(self._ss_mgr)
        self.show_all()

def exig_open_snapshot_file_acb(_action=None):
    snapshot_file_path = dialogue.ask_file_path(_("Snapshot File Path:"))
    if snapshot_file_path:
        with dialogue.comforting_message("Unpickling..."):
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

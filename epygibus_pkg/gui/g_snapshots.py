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

class _ExtractionWidget(Gtk.VBox):
    __g_type_name__ = "_ExtractionWidget"
    def __init__(self, parent=None):
        Gtk.VBox.__init__(self)
        self._target_dir = dialogue.EnterDirPathWidget(prompt=_("Target Directory"), suggestion=os.getcwd(), parent=parent)
        self._start_button = Gtk.Button.new_with_label(_("Start"))
        self.close_button = Gtk.Button.new_with_label(_("Close"))
        self.close_button.set_sensitive(False)
        self.cancel_button = Gtk.Button.new_with_label(_("Cancel"))
        self._overwrite_button = Gtk.CheckButton.new_with_label(_("Overwrite"))
        self._progress_indicator = gutils.ProgessThingy()
        self._stderr_file = gutils.PretendWOFile()
        self._start_button.connect("clicked", self._start_button_bcb)
    def _start_button_bcb(self, _button):
        self.cancel_button.set_sensitive(False)
        self._target_dir.set_sensitive(False)
        self._overwrite_button.set_sensitive(False)
        self._start_button.set_sensitive(False)
        try:
            self._do_extraction()
            self.close_button.set_sensitive(True)
        except excpns.Error as edata:
            self._stderr_file.write(str(edata) + "\n")
            dialogue.report_exception_as_error(edata)
            self.cancel_button.set_sensitive(True)
            self._target_dir.set_sensitive(True)
            self._overwrite_button.set_sensitive(True)
            self._start_button.set_sensitive(True)
    def _do_extraction(self):
        assert False, _("_do_extraction() must be defined in child.")

class _ExtractionDialog(Gtk.Window):
    __g_type_name__ = "_ExtractionDialog"
    WIDGET = None
    def __init__(self, **kwargs):
        Gtk.Window.__init__(self)
        kwargs["parent"] = self
        widget = self.WIDGET(**kwargs)
        widget.close_button.connect("clicked", lambda _button: self.destroy())
        widget.cancel_button.connect("clicked", lambda _button: self.destroy())
        self.add(widget)
        self.show_all()

class DirExtractionWidget(_ExtractionWidget):
    __g_type_name__ = "DirExtractionWidget"
    DST = _("Extracted: {} dirs, {} files, {} symbolic links, {} hard links, {}({}).\n")
    def __init__(self, snapshot_fs, parent=None):
        self._snapshot_fs = snapshot_fs
        _ExtractionWidget.__init__(self, parent=parent)
        self.pack_start(self._target_dir, expand=False, fill=True, padding=0)
        hbox = Gtk.HBox()
        hbox.pack_start(self._overwrite_button, expand=True, fill=True, padding=0)
        hbox.pack_start(self._start_button, expand=True, fill=True, padding=0)
        self.pack_start(hbox, expand=False, fill=True, padding=0)
        self.pack_start(self._progress_indicator, expand=False, fill=True, padding=0)
        self.pack_start(self._stderr_file, expand=True, fill=True, padding=0)
        hbox = Gtk.HBox()
        hbox.pack_start(self.cancel_button, expand=True, fill=True, padding=0)
        hbox.pack_start(self.close_button, expand=True, fill=True, padding=0)
        self.pack_start(hbox, expand=False, fill=True, padding=0)
        self.show_all()
    def _do_extraction(self):
        from .. import utils
        target_dir_path = os.path.abspath(self._target_dir.path)
        overwrite = self._overwrite_button.get_active()
        cs = self._snapshot_fs.copy_contents_to(target_dir_path, overwrite=overwrite, stderr=self._stderr_file, progress_indicator=self._progress_indicator)
        self._stderr_file.write(self.DST.format(cs.dir_count, cs.file_count, cs.soft_link_count, cs.hard_link_count, utils.format_bytes(cs.gross_bytes), utils.format_bytes(cs.net_bytes)))

class DirExtractionDialog(_ExtractionDialog):
    __g_type_name__ = "DirExtractionDialog"
    WIDGET = DirExtractionWidget

DVRow = collections.namedtuple("DVRow", ["fso_data"])

class DVModel(tlview.NamedListStore):
    __g_type_name__ = "DVModel"
    Row = DVRow
    types = DVRow(fso_data=GObject.TYPE_PYOBJECT, )
    def __init__(self, snapshot_fs=None, offset_dir_path=None):
        tlview.NamedListStore.__init__(self)
        self.set_snapshot_fs(snapshot_fs, offset_dir_path)
    def _set_contents(self):
        if self._snapshot_fs is None:
            self.clear()
            return
        offset_subdir_fs = self._snapshot_fs.get_subdir(self._offset_dir_path)
        real_dirs = [DVRow(i) for i in offset_subdir_fs.iterate_subdirs(pre_path=True)]
        dir_links = [DVRow(i) for i in offset_subdir_fs.iterate_subdir_links(pre_path=True)]
        real_files = [DVRow(i) for i in offset_subdir_fs.iterate_files(pre_path=True)]
        file_links = [DVRow(i) for i in offset_subdir_fs.iterate_file_links(pre_path=True)]
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

def stock_id_icon_select_func(fso_data):
    if fso_data.is_dir:
        if fso_data.is_link:
            return icons.STOCK_DIR_LINK
        else:
            return icons.STOCK_DIR
    elif fso_data.is_link:
        return icons.STOCK_FILE_LINK
    else:
        return  icons.STOCK_FILE

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
            tlview.simple_column("", tlview.transform_pixbuf_stock_id_cell(DVModel, "fso_data", stock_id_icon_select_func, xalign=0.0)),
            tlview.simple_column(_("Name"), tlview.transform_data_cell(DVModel, "fso_data", lambda x: x.name, xalign=0.0)),
        ]
    )

class DirectoryView(tlview.ListView):
    __g_type_name__ = "DirectoryView"
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
        return toggle.get_active() or not model.get_value_named(model_iter, "fso_data").is_hidden
    def change_offset_dir_path(self, new_offset_dir_path):
        self._dv_model.change_offset_dir_path(new_offset_dir_path)
    def set_snapshot_fs(self, snapshot_fs, offset_dir_path=None):
        self._dv_model.set_snapshot_fs(snapshot_fs, offset_dir_path)

class SnapshotManagerWidget(Gtk.VBox, actions.CAGandUIManager, actions.CBGUserMixin, dialogue.BusyIndicatorUser):
    __g_type_name__ = "SnapshotManagerWidget"
    def __init__(self, snapshot_fs, busy_indicator=None, parent=None):
        Gtk.VBox.__init__(self)
        self._parent = parent
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
        bbox = self.button_groups.create_action_button_box(["snapshot_dir_show_hidden", "snapshot_extract_current_dir"])
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
                 None),
                ("snapshot_extract_current_dir", Gtk.Button.new_with_label(_("Extract")),
                 _("Extract this directory's files and directories to a nominated directory."),
                 self._extract_this_dir_bcb),
            ])
        self.button_groups[AC_ABOVE_BASE_OFFSET].add_buttons(
            [
                ("snapshot_dir_go_up", Gtk.Button.new_from_icon_name(Gtk.STOCK_GO_UP, Gtk.IconSize.BUTTON),
                 _("Change displayed directory to parent of current displayed directory."),
                 self._change_dir_up_bcb),
            ])
    def _double_click_cb(self, tree_view, tree_path, tree_view_column):
        # TODO: build capability to work with filters into tlview
        model = tree_view.get_model()
        named_model = model.get_model()
        row = named_model.Row(*model[tree_path])
        if row.fso_data.is_dir:
            if row.fso_data.is_link:
                # TODO: think about handling links to links here
                if not self._snapshot_fs.contains_subdir(row.fso_data.tgt_abs_path):
                    dialogue.inform_user(_("Symbolic link target {} is not stored in this snapshot").format(row.fso_data.tgt_abs_path), parent=self._parent)
                    return
                self._current_offset_dir_path = row.fso_data.tgt_abs_path
            else:
                self._current_offset_dir_path = row.fso_data.path
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
    def _extract_this_dir_bcb(self, _button):
        dir_snapshot_fs = self._snapshot_fs.get_subdir(self._current_offset_dir_path)
        dialog = DirExtractionDialog(snapshot_fs=dir_snapshot_fs)
        dialog.show()

class ExigSnapshotDialog(Gtk.Window):
    __g_type_name__ = "ExigSnapshotDialog"
    def __init__(self, snapshot_fs, parent=None):
        title = _("Snapshot Exigency: {}:{}").format(snapshot_fs.archive_name, snapshot_fs.snapshot_name)
        Gtk.Window.__init__(self, title=title, type=Gtk.WindowType.TOPLEVEL, parent=parent)
        self._ss_mgr = SnapshotManagerWidget(snapshot_fs, parent=self)
        self.add(self._ss_mgr)
        self.show_all()

def exig_open_snapshot_file_acb(_action=None):
    snapshot_file_path = dialogue.ask_file_path(_("Snapshot File Path:"))
    if snapshot_file_path:
        try:
            snapshot_fs = snapshot.get_snapshot_fs_fm_file(snapshot_file_path)
        except (excpns.Error, OSError) as edata:
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

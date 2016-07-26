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
from . import table
from . import auto_update
from . import g_archives

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
        self._progress_indicator = gutils.ProgressThingy()
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

class DirRestorationWidget(_ExtractionWidget):
    __g_type_name__ = "DirRestorationWidget"
    DST = _("Restored: {} dirs, {} files, {} symbolic links, {} hard links, {}({}).\n")
    def __init__(self, snapshot_fs, parent=None):
        self._snapshot_fs = snapshot_fs
        _ExtractionWidget.__init__(self, parent=parent)
        label_text = _("Restoring: contents of \"{}\" from \"{}\" snapshot in archive \"{}\".\n").format(snapshot_fs.path, snapshot_fs.snapshot_name, snapshot_fs.archive_name)
        self.pack_start(Gtk.Label(label_text), expand=False, fill=True, padding=0)
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
        overwrite = self._overwrite_button.get_active()
        cs = self._snapshot_fs.restore(overwrite=overwrite, stderr=self._stderr_file, progress_indicator=self._progress_indicator)
        self._stderr_file.write(self.DST.format(cs.dir_count, cs.file_count, cs.soft_link_count, cs.hard_link_count, utils.format_bytes(cs.gross_bytes), utils.format_bytes(cs.net_bytes)))

class DirRestorationDialog(_ExtractionDialog):
    __g_type_name__ = "DirRestorationDialog"
    WIDGET = DirRestorationWidget

DVRow = collections.namedtuple("DVRow", ["fso_data"])

class DVModel(Gtk.ListStore):
    __g_type_name__ = "DVModel"
    def __init__(self, snapshot_fs=None, offset_dir_path=None):
        Gtk.ListStore.__init__(self, GObject.TYPE_PYOBJECT)
        self.set_snapshot_fs(snapshot_fs, offset_dir_path)
    def _set_contents(self):
        if self._snapshot_fs is None:
            self.clear()
            return
        offset_subdir_fs = self._snapshot_fs.get_subdir(self._offset_dir_path)
        real_dirs = list(offset_subdir_fs.iterate_subdirs(pre_path=True))
        dir_links = list(offset_subdir_fs.iterate_subdir_links(pre_path=True))
        real_files = list(offset_subdir_fs.iterate_files(pre_path=True))
        file_links = list(offset_subdir_fs.iterate_file_links(pre_path=True))
        self.clear()
        for item in sorted(real_dirs + dir_links) + sorted(real_files + file_links):
            self.append([item])
    def change_offset_dir_path(self, new_offset_dir_path):
        self._offset_dir_path = new_offset_dir_path
        self._set_contents()
    def set_snapshot_fs(self, snapshot_fs, offset_dir_path=None):
        assert (snapshot_fs and offset_dir_path) or (not snapshot_fs and not offset_dir_path)
        self._snapshot_fs = snapshot_fs
        self._offset_dir_path = offset_dir_path
        self._set_contents()

def dv_icon_set_func(treeviewcolumn, cell, model, tree_iter, *args):
    fso_data = model[tree_iter][0]
    if fso_data.is_dir:
        if fso_data.is_link:
            icon = icons.STOCK_DIR_LINK
        else:
            icon = icons.STOCK_DIR
    elif fso_data.is_link:
        icon = icons.STOCK_FILE_LINK
    else:
        icon = icons.STOCK_FILE
    cell.set_property("stock_id", icon)

def dv_name_set_func(treeviewcolumn, cell, model, tree_iter, *args):
    fso_data = model[tree_iter][0]
    cell.set_property("text", fso_data.name)

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
            tlview.ColumnSpec(
                title="",
                properties={"expand": False, "resizable" : True},
                cells=[
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=Gtk.CellRendererPixbuf,
                            expand=False,
                            start=True,
                            properties={"xalign": 0.0},
                        ),
                        cell_data_function_spec=tlview.CellDataFunctionSpec(function=dv_icon_set_func),
                    ),
                ],
            ),
            tlview.ColumnSpec(
                title=_("Name"),
                properties={"expand": False, "resizable" : True},
                cells=[
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=Gtk.CellRendererText,
                            expand=False,
                            start=True,
                            properties={"editable" : False, "xalign": 0.0},
                        ),
                        cell_data_function_spec=tlview.CellDataFunctionSpec(function=dv_name_set_func),
                    )
                ],
            )
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
        return toggle.get_active() or not model[model_iter][0].is_hidden
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
        bbox = self.button_groups.create_action_button_box(["snapshot_dir_show_hidden", "snapshot_extract_current_dir", "snapshot_restore_current_dir"])
        self.pack_start(bbox, expand=False, fill=True, padding=0)
        self._dir_view.connect("row_activated", self._double_click_cb)
        self._update_above_base_offset_status()
        self.show_all()
    @property
    def archive_name(self):
        return self._snapshot_fs.archive_name
    @property
    def snapshot_name(self):
        return self._snapshot_fs.snapshot_name
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
                ("snapshot_restore_current_dir", Gtk.Button.new_with_label(_("Restore")),
                 _("Restore this directory's files and directories to the file system."),
                 self._restore_this_dir_bcb),
            ])
        self.button_groups[AC_ABOVE_BASE_OFFSET].add_buttons(
            [
                ("snapshot_dir_go_up", Gtk.Button.new_from_icon_name(Gtk.STOCK_GO_UP, Gtk.IconSize.BUTTON),
                 _("Change displayed directory to parent of current displayed directory."),
                 self._change_dir_up_bcb),
            ])
    def _double_click_cb(self, tree_view, tree_path, tree_view_column):
        fso_data = tree_view.get_model()[tree_path][0]
        if fso_data.is_dir:
            if fso_data.is_link:
                # TODO: think about handling links to links here
                if not self._snapshot_fs.contains_subdir(fso_data.tgt_abs_path):
                    dialogue.inform_user(_("Symbolic link target {} is not stored in this snapshot").format(fso_data.tgt_abs_path), parent=self._parent)
                    return
                self._current_offset_dir_path = fso_data.tgt_abs_path
            else:
                self._current_offset_dir_path = fso_data.path
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
    def _restore_this_dir_bcb(self, _button):
        dir_snapshot_fs = self._snapshot_fs.get_subdir(self._current_offset_dir_path)
        dialog = DirRestorationDialog(snapshot_fs=dir_snapshot_fs)
        dialog.show()

class ExigSnapshotDialog(Gtk.Window):
    __g_type_name__ = "ExigSnapshotDialog"
    def __init__(self, snapshot_fs, parent=None):
        title = _("Snapshot Exigency: {}:{}").format(snapshot_fs.archive_name, snapshot_fs.snapshot_name)
        Gtk.Window.__init__(self, title=title, type=Gtk.WindowType.TOPLEVEL, parent=parent)
        self._ss_mgr = SnapshotManagerWidget(snapshot_fs, parent=self)
        self.add(self._ss_mgr)
        self.show_all()

class SSNameTableData(table.TableData):
    def __init__(self, archive_name):
        table.TableData.__init__(self, archive_name=archive_name)
    @property
    def archive_name(self):
        return self._kwargs["archive_name"]
    def _get_data_text(self, h):
        if self.archive_name is None:
            return []
        ss_name_list = snapshot.get_snapshot_name_list(self.archive_name, reverse=True)
        h.update(str(ss_name_list).encode())
        return ss_name_list
    def _finalize(self, pdt):
        self._ss_name_list = pdt
    def iter_rows(self):
        for ss_name in self._ss_name_list:
            yield ss_name

class SSNameListModel(Gtk.ListStore):
    __g_type_name__ = "SSNameModel"
    REPOPULATE_EVENTS = 0
    UPDATE_EVENTS = 0
    def __init__(self, archive_name=None):
        Gtk.ListStore.__init__(self, GObject.TYPE_STRING, GObject.TYPE_BOOLEAN)
        self.set_archive_name(archive_name)
        auto_update.register_cb(self._auto_update_cb)
    @property
    def archive_name(self):
        return self._archive_name
    def _auto_update_cb(self, events_so_far, args):
        if not self._ss_list_db.is_current:
            self._update_contents(reset_only=True)
        # NB changes here are of no interest to others
        return 0
    def _set_contents(self):
        self._ss_list_db =  self._get_ss_list_db(reset_only=False)
        self.clear()
        for row in self._ss_list_db.iter_rows():
            self.append(row)
    def _update_contents(self, reset_only=True):
        # NB: this process relies on fact all NEW rows will have a name
        # greater than any in the model and model/list are both ordered
        # in descending order of time
        self._ss_list_db = self._get_ss_list_db(reset_only=reset_only)
        model_iter = self.get_iter_first()
        for row in self._ss_list_db.iter_rows():
            model_row_name = self[model_iter][0]
            if model_row_name == row[0]:
                self.set(model_iter, [1], row[1:])
                model_iter = self.iter_next(model_iter)
            elif model_row_name < row[0]:
                self.insert_before(model_iter, row)
            else:
                self.remove(model_iter)
        while model_iter and self.iter_is_valid(model_iter):
            self.remove(model_iter)
    def set_archive_name(self, archive_name=None):
        self._archive_name = archive_name
        self._set_contents()
    def compressed_toggle_cb(self, toggle, model_path):
        row = self[model_path]
        snapshot.toggle_named_snapshot_compression(self.archive_name, row[0])
        self._update_contents(False)
    def _get_ss_list_db(self, reset_only):
        return self._ss_list_db.reset() if reset_only else SSNameTableData(self._archive_name)

def ssnl_specification(model):
    return tlview.ViewSpec(
        properties={
            "enable-grid-lines" : False,
            "reorderable" : False,
            "rules_hint" : False,
            "headers-visible" : True,
        },
        selection_mode = Gtk.SelectionMode.MULTIPLE,
        columns = [
            tlview.ColumnSpec(
                title=_("Snapshot Time (Local)"),
                properties={"expand": False, "resizable" : False},
                cells=[
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=Gtk.CellRendererText,
                            expand=False,
                            start=True,
                            properties={"editable" : False, "xalign" : 0.0, "width-chars" : 24, "max-width-chars" : 24},
                        ),
                        cell_data_function_spec=None,
                        attributes = {"text" : 0}
                    )
                ],
            ),
            tlview.ColumnSpec(
                title=_("Cmprd"),
                properties={"expand": False, "resizable" : False},
                cells=[
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=Gtk.CellRendererToggle,
                            expand=False,
                            start=True,
                            signal_handlers = {"toggled" : model.compressed_toggle_cb},
                            properties={"xalign": 0.5},
                        ),
                        cell_data_function_spec=None,
                        attributes = {"active" : 1}
                    )
                ],
            )
        ]
    )

class SSNameListView(tlview.View, actions.CAGandUIManager):
    __g_type_name__ = "SSNameListView"
    PopUp = None
    Model = SSNameListModel
    specification = ssnl_specification
    UI_DESCR = '''
    <ui>
      <popup name="snapshot_name_list_popup">
        <menuitem action="delete_selected_snapshots"/>
      </popup>
    </ui>
    '''
    def __init__(self, archive_name, size_req=None, parent=None):
        self._parent = parent
        model = SSNameListModel(archive_name)
        tlview.View.__init__(self, model=model, size_req=size_req)
        self.connect("button_press_event", tlview.clear_selection_cb)
        self.connect("key_press_event", tlview.clear_selection_cb)
        actions.CAGandUIManager.__init__(self, selection=self.get_selection(), popup="/snapshot_name_list_popup")
    @property
    def archive_name(self):
        return self.get_model().archive_name
    @archive_name.setter
    def archive_name(self, archive_name):
        self.get_model().set_archive_name(archive_name)
    def get_selected_snapshots(self):
        model, paths = self.get_selection().get_selected_rows()
        return [model[p][0] for p in paths]
    def populate_action_groups(self):
        self.action_groups[actions.AC_SELN_MADE].add_actions(
            [
                ("delete_selected_snapshots", icons.STOCK_REPO_DELETE, _("Delete"), None,
                  _("Delete the selected snapshot(s)."),
                  lambda _action=None: self._delete_selected_snapshots()
                )
            ])
    def _delete_selected_snapshots(self):
        selected_snapshots = self.get_selected_snapshots()
        remainder = len(self.model) - len(selected_snapshots)
        DeleteSnapshotsDialog(self.archive_name, selected_snapshots, remainder, self._parent).run()

class DeleteSnapshotsDialog(Gtk.Dialog):
    def __init__(self, archive_name, snapshot_names, leaving_behind, parent=None):
        self._archive_name = archive_name
        self._snapshot_names = snapshot_names
        parent = parent if parent else dialogue.main_window
        Gtk.Dialog.__init__(self, _("Delete snapshots."), parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_YES, Gtk.ResponseType.YES, Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        self.set_response_sensitive(Gtk.ResponseType.CLOSE, False)
        c_text = _("About to delete {} snapshots from \"{}\" archive leavin {}. Continue?").format(len(snapshot_names), archive_name, leaving_behind)
        self._count_indicator = gutils.ProgressThingy()
        self._count_indicator.set_expected_total(len(self._snapshot_names))
        self._ss_progress_indicator = gutils.ProgressThingy()
        self._ss_name_label = Gtk.Label("                    ")
        vbox = Gtk.VBox()
        vbox.pack_start(self._count_indicator, expand=False, fill=True, padding=0)
        hbox = Gtk.HBox()
        hbox.pack_start(self._ss_name_label, expand=False, fill=True, padding=0)
        hbox.pack_start(self._ss_progress_indicator, expand=True, fill=True, padding=0)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        vbox.pack_start(Gtk.Label(c_text), expand=True, fill=True, padding=0)
        self.get_content_area().add(vbox)
        self.connect("response", self._response_cb)
        self.show_all()
    def _response_cb(self, _dialog, response_id):
        if response_id in [Gtk.ResponseType.CANCEL, Gtk.ResponseType.CLOSE]:
            self.destroy()
            return
        for response_id in [Gtk.ResponseType.CANCEL, Gtk.ResponseType.YES]:
            self.set_response_sensitive(response_id, False)
        for snapshot_name in self._snapshot_names:
            self._ss_name_label.set_text(snapshot_name)
            snapshot.delete_named_snapshot(self._archive_name, snapshot_name, self._ss_progress_indicator)
            self._count_indicator.increment_count()
        self._count_indicator.finished()
        self.set_response_sensitive(Gtk.ResponseType.CLOSE, True)

class ArchiveSSListWidget(Gtk.VBox):
    __g_type_name__ = "ArchiveSSListWidget"
    def __init__(self):
        Gtk.VBox.__init__(self)
        self._archive_selector = g_archives.ArchiveComboBox()
        self._snapshot_list = SSNameListView(self._archive_selector.get_active_text(), size_req=(200, 640))
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_("Archive: ")), expand=False, fill=True, padding=0)
        hbox.pack_start(self._archive_selector, expand=True, fill=True, padding=0)
        self.pack_start(hbox, expand=False, fill=True, padding=0)
        self.pack_start(gutils.wrap_in_scrolled_window(self._snapshot_list, policy=(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)), expand=True, fill=True, padding=0)
        self._archive_selector.connect("changed", self._archive_selection_change_cb)
        self.show_all()
    @property
    def snapshot_list(self):
        return self._snapshot_list
    def _archive_selection_change_cb(self, combo):
        self._snapshot_list.archive_name = combo.get_active_text()

class SnapshotsMgrWidget(Gtk.HBox):
    __g_type_name__ = "SnapshotMgrWidget"
    def __init__(self):
        Gtk.HBox.__init__(self)
        self._snapshot_selector = ArchiveSSListWidget()
        self._snapshot_selector.snapshot_list.connect("row_activated", self._open_snapshot_cb)
        self._notebook = gutils.NotebookWithDelete(tab_delete_tooltip=_("Close this snapshot."))
        self._notebook.set_scrollable(True)
        self._notebook.popup_enable()
        self.pack_start(self._snapshot_selector, expand=False, fill=True, padding=0)
        self.pack_start(self._notebook, expand=True, fill=True, padding=0)
        self.show_all()
    def _open_snapshot_cb(self, tree_view, tree_path, tree_view_column):
        # TODO: close snapshots if their file disappears
        archive_name = tree_view.archive_name
        snapshot_name = tree_view.get_model()[tree_path][0]
        for page_num, existing_page in self._notebook.iterate_pages():
            if existing_page.archive_name == archive_name:
                if existing_page.snapshot_name == snapshot_name:
                    self._notebook.set_current_page(page_num)
                    return
        snapshot_fs = snapshot.get_named_snapshot_fs(archive_name, snapshot_name)
        tab_label = Gtk.Label(archive_name + ":" + snapshot_name)
        menu_label = Gtk.Label(archive_name + ":" + snapshot_name)
        ss_mgr = SnapshotManagerWidget(snapshot_fs)
        page_num = self._notebook.append_deletable_page_menu(ss_mgr, tab_label, menu_label)
        if page_num != -1:
            self._notebook.set_current_page(page_num)

# class independent actions
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
        ("snapshot_exigency_menu", None, _("Snapshot Exigencies"), None, _("Mechanisms for handling cases where configuration files have been lost.")),
        ("exig_open_snapshot_file", icons.STOCK_OPEN_SNAPSHOT_FILE, _("Open Snapshot File"), None,
         _("(Exigency) open a snapshot file directly. Should only be used when configuration files have been lost."),
         exig_open_snapshot_file_acb
        ),
    ])

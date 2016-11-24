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

from .. import config
from .. import utils
from .. import excpns
from .. import snapshot
from ..bab import enotify

from ..gtx import actions
from ..gtx import auto_update
from ..gtx import table
from . import icons
from ..gtx import tlview
from ..gtx import dialogue
from ..gtx import gutils
from ..gtx import recollect
from ..gtx import text_edit

from . import g_repos

AC_ARCHIVES_AVAILABLE = actions.ActionCondns.new_flag()
NE_NEW_ARCHIVE, NE_DELETE_ARCHIVE, NE_ARCHIVE_POPN_CHANGE = enotify.new_event_flags_and_mask(2)
NE_ARCHIVE_SPEC_CHANGE = enotify.new_event_flag()

_n_archives = 0
_archive_name_hash_digest = None

def get_archive_name_hash_digest_etc():
    import hashlib
    archive_name_list = config.get_archive_name_list()
    return (hashlib.sha1(str(archive_name_list).encode()).digest(), len(archive_name_list),)

def get_archive_available_condn():
    if _n_archives:
        return actions.MaskedCondns(AC_ARCHIVES_AVAILABLE, AC_ARCHIVES_AVAILABLE)
    else:
        return actions.MaskedCondns(0, AC_ARCHIVES_AVAILABLE)

def _ne_num_archive_change_cb(**kwargs):
    global _n_archives
    old_n_archives = _n_archives
    global _archive_name_hash_digest
    old_archive_name_hash_digest = _archive_name_hash_digest
    _archive_name_hash_digest, _n_archives = get_archive_name_hash_digest_etc()
    if old_n_archives != _n_archives and not (old_n_archives and _n_archives):
        actions.CLASS_INDEP_AGS.update_condns(get_archive_available_condn())

_ne_num_archive_change_cb()

enotify.add_notification_cb(NE_ARCHIVE_POPN_CHANGE, _ne_num_archive_change_cb)

def _auto_update_cb(events_so_far, _args):
    if events_so_far & NE_ARCHIVE_POPN_CHANGE or get_archive_name_hash_digest_etc()[0] == _archive_name_hash_digest:
        return 0
    return NE_ARCHIVE_POPN_CHANGE

auto_update.register_cb(_auto_update_cb)

Archive = collections.namedtuple("Archive", ["name", "repo_name", "snapshot_dir_path", "includes", "exclude_dir_globs", "exclude_file_globs", "skip_broken_soft_links", "compress_default"])

class ArchiveTableData(table.TableData):
    def _get_data_text(self, h):
        archive_spec_list = config.get_archive_spec_list()
        h.update(str(archive_spec_list).encode())
        return archive_spec_list
    def _finalize(self, pdt):
        self._rows = pdt
    #def iter_rows(self):
        #for archive_spec in sorted(self._rows):
            #yield archive_spec

class ArchiveListModel(table.MapManagedTableView.MODEL):
    __g_type_name__ = "ArchiveListModel"
    ROW = config.Archive
    TYPES = ROW(
        name=GObject.TYPE_STRING,
        repo_name=GObject.TYPE_STRING,
        snapshot_dir_path=GObject.TYPE_STRING,
        includes=GObject.TYPE_PYOBJECT,
        exclude_dir_globs=GObject.TYPE_PYOBJECT,
        exclude_file_globs=GObject.TYPE_PYOBJECT,
        skip_broken_soft_links=GObject.TYPE_BOOLEAN,
        compress_default=GObject.TYPE_BOOLEAN,
    )

def _archive_list_spec():
    specification = tlview.ViewSpec(
        properties={
            "enable-grid-lines" : False,
            "reorderable" : False,
            "rules_hint" : False,
            "headers-visible" : True,
        },
        selection_mode=Gtk.SelectionMode.SINGLE,
        columns=[
            tlview.simple_column(_("Name"), tlview.fixed_text_cell(ArchiveListModel, "name", 0.0)),
            tlview.simple_column(_("Repository"), tlview.fixed_text_cell(ArchiveListModel, "repo_name", 0.0)),
            tlview.simple_column(_("Compressed"), tlview.fixed_toggle_cell(ArchiveListModel, "compress_default", 0.0)),
            tlview.simple_column(_("Skip Broken"), tlview.fixed_toggle_cell(ArchiveListModel, "skip_broken_soft_links", 0.0)),
            tlview.simple_column(_("#Includes"), tlview.transform_data_cell(ArchiveListModel, "includes", lambda x : str(len(x)), xalign=1.0)),
            tlview.simple_column(_("#Dir Excludes"), tlview.transform_data_cell(ArchiveListModel, "exclude_dir_globs", lambda x : str(len(x)), xalign=1.0)),
            tlview.simple_column(_("#File_Excludes"), tlview.transform_data_cell(ArchiveListModel, "exclude_file_globs", lambda x : str(len(x)), xalign=1.0)),
            tlview.simple_column(_("Snapshot Directory"), tlview.fixed_text_cell(ArchiveListModel, "snapshot_dir_path", 0.0)),
        ]
    )
    return specification

class ArchiveListView(table.MapManagedTableView):
    __g_type_name__ = "ArchiveListView"
    MODEL = ArchiveListModel
    PopUp = "/archive_list_view_popup"
    SET_EVENTS = 0
    REFRESH_EVENTS = NE_ARCHIVE_POPN_CHANGE | NE_ARCHIVE_SPEC_CHANGE
    AU_REQ_EVENTS = NE_ARCHIVE_SPEC_CHANGE
    UI_DESCR = """
    <ui>
      <popup name="archive_list_view_popup">
        <menuitem action="edit_selected_snapshot_inclusions"/>
        <menuitem action="edit_selected_snapshot_dir_exclusions"/>
        <menuitem action="edit_selected_snapshot_file_exclusions"/>
      </popup>
    </ui>
    """
    SPECIFICATION = _archive_list_spec()
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        self.set_contents()
    def get_selected_archive(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_value_named(store_iter, "name")
    def _get_table_db(self):
        return ArchiveTableData()
    def populate_action_groups(self):
        self.action_groups[actions.AC_SELN_UNIQUE].add_actions(
            [
                ("edit_selected_snapshot_inclusions", icons.STOCK_EDIT_INCLUDES, _("Edit Inclusions"), None,
                  _("Edit the inclusions for the selected snapshot."),
                  lambda _action=None: IncludesEditDialog(self.get_selected_archive()).show()
                ),
                ("edit_selected_snapshot_file_exclusions", icons.STOCK_EDIT_EXCLUDE_FILES, _("Edit File Exclusions"), None,
                  _("Edit the file exclusions for the selected snapshot."),
                  lambda _action=None: FileExcludesEditDialog(self.get_selected_archive()).show()
                ),
                ("edit_selected_snapshot_dir_exclusions", icons.STOCK_EDIT_EXCLUDE_DIRS, _("Edit Directory Exclusions"), None,
                  _("Edit the directory exclusions for the selected snapshot."),
                  lambda _action=None: DirExcludesEditDialog(self.get_selected_archive()).show()
                )
            ])

class ArchiveListWidget(table.TableWidget):
    __g_type_name__ = "ArchiveListWidget"
    View = ArchiveListView

class IncludesModel(tlview.NamedListStore):
    __g_type_name__ = "IncludesModel"
    ROW = collections.namedtuple("ROW", ["included_path"])
    TYPES = ROW(included_path=GObject.TYPE_STRING)

class IncludesView(tlview.View, actions.CBGUserMixin):
    __g_type_name__ = "IncludesView"
    MODEL = IncludesModel
    SPECIFICATION = tlview.ViewSpec(
        properties={
            "enable-grid-lines" : True,
            "reorderable" : True,
            "headers-visible" : False,
        },
        selection_mode=Gtk.SelectionMode.MULTIPLE,
        columns=[
            tlview.ColumnSpec(
                title=_("Included Path"),
                properties={"expand" : True},
                cells=[
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=Gtk.CellRendererText,
                            expand=False,
                            start=True,
                            properties={"editable" : False},
                        ),
                        cell_data_function_spec=None,
                        attributes={"text" : MODEL.col_index("included_path")}
                    ),
                ],
            ),
        ]
    )
    def __init__(self):
        tlview.View.__init__(self, size_req=(320, 160))
        actions.CBGUserMixin.__init__(self, self.get_selection())
    def populate_button_groups(self):
        self.button_groups[actions.AC_DONT_CARE].add_buttons(
            [
                ("table_add_file_path", Gtk.Button.new_with_label(_("Append File")),
                 _("Append a new file path to the includes table"),
                 [("clicked", self._add_file_path_bcb)]
                ),
                ("table_add_dir_path", Gtk.Button.new_with_label(_("Append Directory")),
                 _("Append a new directory path to the includes table"),
                 [("clicked", self._add_dir_path_bcb)]
                ),
            ])
        self.button_groups[actions.AC_SELN_MADE].add_buttons(
            [
                ("table_delete_selection", Gtk.Button.new_from_stock(Gtk.STOCK_DELETE),
                 _("Delete selected row(s)"),
                 [("clicked", self._delete_selection_bcb)]
                ),
                ("table_insert_file_path", Gtk.Button.new_with_label(_("Insert File")),
                 _("Insert a new file path before the selected row(s)"),
                 [("clicked", self._insert_file_path_bcb)]
                ),
                ("table_insert_dir_path", Gtk.Button.new_with_label(_("Insert Directory")),
                 _("Insert a new directory path before the selected row(s)"),
                 [("clicked", self._insert_dir_path_bcb)]
                ),
            ])
    def get_included_paths(self):
        return [row.included_path for row in self.model.named()]
    def _add_file_path_bcb(self, _button=None):
        file_path = dialogue.select_file(_("Select File to Add"), absolute=True)
        if file_path:
            self.model.append(self.MODEL.ROW(file_path))
    def _add_dir_path_bcb(self, _button=None):
        dir_path = dialogue.select_directory(_("Select Directory to Add"), absolute=True)
        if dir_path:
            self.model.append(self.MODEL.ROW(dir_path))
    def _insert_file_path_bcb(self, _button=None):
        file_path = dialogue.select_file(_("Select File to Insert"), absolute=True)
        if file_path:
            tlview.insert_before_selection(self.get_selection(), self.MODEL.ROW(file_path))
    def _insert_dir_path_bcb(self, _button=None):
        dir_path = dialogue.select_directory(_("Select Directory to Insert"), absolute=True)
        if dir_path:
            tlview.insert_before_selection(self.get_selection(), self.MODEL.ROW(dir_path))
    def _delete_selection_bcb(self, _button=None):
        tlview.delete_selection(self.get_selection())

class IncludesTable(actions.ClientAndButtonsWidget):
    __g_type_name__ = "IncludesTable"
    CLIENT = IncludesView
    BUTTONS = ["table_add_dir_path", "table_insert_dir_path", "table_add_file_path", "table_insert_file_path", "table_delete_selection"]
    SCROLLABLE = True
    def get_included_paths(self):
        return self.client.get_included_paths()

# TODO: combine IncludesEditView and IncludesView into single class
class IncludesEditView(table.EditableEntriesView):
    __g_type_name__ = "IncludesEditView"
    MODEL = IncludesModel
    SPECIFICATION = tlview.ViewSpec(
        properties={
            "enable-grid-lines" : True,
            "reorderable" : True,
            "headers-visible" : False,
        },
        selection_mode=Gtk.SelectionMode.MULTIPLE,
        columns=[
            tlview.ColumnSpec(
                title=_("Included Path"),
                properties={"expand" : True},
                cells=[
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=Gtk.CellRendererText,
                            expand=False,
                            start=True,
                            properties={"editable" : False},
                        ),
                        cell_data_function_spec=None,
                        attributes={"text" : MODEL.col_index("included_path")}
                    ),
                ],
            ),
        ]
    )
    def __init__(self, archive_name):
        self._archive_name = archive_name
        tlview.View.__init__(self, size_req=(320, 160))
        actions.CBGUserMixin.__init__(self, self.get_selection())
        self.set_contents()
    def populate_button_groups(self):
        table.EditableEntriesView.populate_button_groups(self)
        self.button_groups[actions.AC_DONT_CARE].add_buttons(
            [
                ("table_add_file_path", Gtk.Button.new_with_label(_("Append File")),
                 _("Append a new file path to the includes table"),
                 [("clicked", self._add_file_path_bcb)]
                ),
                ("table_add_dir_path", Gtk.Button.new_with_label(_("Append Directory")),
                 _("Append a new directory path to the includes table"),
                 [("clicked", self._add_dir_path_bcb)]
                ),
            ])
        self.button_groups[actions.AC_SELN_MADE].add_buttons(
            [
                ("table_delete_selection", Gtk.Button.new_from_stock(Gtk.STOCK_DELETE),
                 _("Delete selected row(s)"),
                 [("clicked", self._delete_selection_bcb)]
                ),
                ("table_insert_file_path", Gtk.Button.new_with_label(_("Insert File")),
                 _("Insert a new file path before the selected row(s)"),
                 [("clicked", self._insert_file_path_bcb)]
                ),
                ("table_insert_dir_path", Gtk.Button.new_with_label(_("Insert Directory")),
                 _("Insert a new directory path before the selected row(s)"),
                 [("clicked", self._insert_dir_path_bcb)]
                ),
            ])
    def get_included_paths(self):
        return [row.included_path for row in self.model.named()]
    def _add_file_path_bcb(self, _button=None):
        file_path = dialogue.select_file(_("Select File to Add"), absolute=True)
        if file_path:
            self.model.append(self.MODEL.ROW(file_path))
            self._set_modified(True)
    def _add_dir_path_bcb(self, _button=None):
        dir_path = dialogue.select_directory(_("Select Directory to Add"), absolute=True)
        if dir_path:
            self.model.append(self.MODEL.ROW(dir_path))
            self._set_modified(True)
    def _insert_file_path_bcb(self, _button=None):
        file_path = dialogue.select_file(_("Select File to Insert"), absolute=True)
        if file_path:
            tlview.insert_before_selection(self.get_selection(), self.MODEL.ROW(file_path))
            self._set_modified(True)
    def _insert_dir_path_bcb(self, _button=None):
        dir_path = dialogue.select_directory(_("Select Directory to Insert"), absolute=True)
        if dir_path:
            tlview.insert_before_selection(self.get_selection(), self.MODEL.ROW(dir_path))
            self._set_modified(True)
    def _delete_selection_bcb(self, _button=None):
        tlview.delete_selection(self.get_selection())
        self._set_modified(True)
    def _fetch_contents(self):
        return [self.MODEL.ROW(line) for line in config.read_includes_file_lines(self._archive_name)]
    def apply_changes(self):
        config.write_includes_file_lines(self._archive_name, self.get_included_paths())
        self._set_modified(False)

class IncludesEditTable(actions.ClientAndButtonsWidget):
    __g_type_name__ = "IncludesEditTable"
    CLIENT = IncludesEditView
    BUTTONS = ["table_undo_changes", "table_add_dir_path", "table_insert_dir_path", "table_add_file_path", "table_insert_file_path", "table_delete_selection", "table_apply_changes"]
    SCROLLABLE = True

class IncludesEditDialog(Gtk.Dialog):
    __g_type_name__ = "IncludesEditDialog"
    def __init__(self, archive_name, parent=None):
        title = _("Edit \"{}\" archive\'s inclusions.").format(archive_name)
        parent = parent if parent else dialogue.main_window
        Gtk.Dialog.__init__(self, title=title, parent=parent)
        self.new_archive_widget = IncludesEditTable(archive_name=archive_name)
        self.get_content_area().pack_start(self.new_archive_widget, expand=True, fill=True, padding=0)
        self.show_all()

class ExcludesBuffer(text_edit.ModifyUndoSaveBuffer):
    __g_type_name__ = "ExcludesBuffer"
    def __init__(self):
        text_edit.ModifyUndoSaveBuffer.__init__(self)
    def populate_button_groups(self):
        self.button_groups[actions.AC_DONT_CARE].add_buttons(
            [
                ("insert_dir_path", Gtk.Button.new_with_label(_("Insert Directory Path")),
                 _("Browse for and insert a directory path at the text cursor."),
                 [("clicked", self._insert_dir_path_bcb)]
                ),
                ("insert_file_path", Gtk.Button.new_with_label(_("Insert File Path")),
                 _("Browse for and insert a file path at the text cursor."),
                 [("clicked", self._insert_file_path_bcb)]
                ),
            ])
    def _insert_dir_path_bcb(self, _button=None):
        dir_path = dialogue.select_directory(_("Select Directory to Insert"), absolute=True)
        if dir_path:
            self.insert_at_cursor(dir_path + "\n")
            self.set_modified(True)
    def _insert_file_path_bcb(self, _button=None):
        file_path = dialogue.select_file(_("Select Directory to Insert"), absolute=True)
        if file_path:
            self.insert_at_cursor(file_path + "\n")
            self.set_modified(True)
    def get_lines(self):
        return [line.rstrip() for line in self.get_text(self.get_start_iter(), self.get_end_iter(), False).splitlines(False)]

class ExcludesView(Gtk.TextView):
    __g_type_name__ = "ExcludesView"
    BUFFER = ExcludesBuffer
    def __init__(self, **kwargs):
        bfr = self.BUFFER(**kwargs)
        Gtk.TextView.__init__(self, buffer=bfr)
    def get_lines(self):
        return self.get_buffer().get_lines()
    def create_button_box(self, button_name_list):
        return self.get_buffer().create_button_box(button_name_list)

class DirExcludesWidget(actions.ClientAndButtonsWidget):
    __g_type_name__ = "DirExcludesWidget"
    CLIENT = ExcludesView
    BUTTONS = ["insert_dir_path"]
    SCROLLABLE = True
    def get_lines(self):
        return self.client.get_lines()

class FileExcludesWidget(actions.ClientAndButtonsWidget):
    __g_type_name__ = "FileExcludesWidget"
    CLIENT = ExcludesView
    BUTTONS = ["insert_file_path"]
    SCROLLABLE = True
    def get_lines(self):
        return self.client.get_lines()

class DirExcludesEditBuffer(ExcludesBuffer):
    __g_type_name__ = "DirExcludesEditBuffer"
    def __init__(self, archive_name):
        self._archive_name = archive_name
        ExcludesBuffer.__init__(self)
        self._load_content()
    def populate_button_groups(self):
        ExcludesBuffer.populate_button_groups(self)
        self.button_groups[self.AC_MODIFIED].add_buttons(
            [
                ("apply_changes", Gtk.Button.new_with_label(_("Apply")),
                 _("Apply the pending changes to the specification."),
                 [("clicked", lambda _button: self._write_content())]
                ),
                ("undo_changes", Gtk.Button.new_with_label(_("Undo")),
                 _("Undo the pending changes to the specification."),
                 [("clicked", lambda _button: self._load_content())]
                ),
            ])
    def _load_content(self):
        lines = config.read_exclude_dir_lines(self._archive_name)
        if lines:
            self.set_text(os.linesep.join(lines) + os.linesep)
        else:
            self.set_text("")
        self.set_modified(False)
    def _write_content(self):
        config.write_exclude_dir_lines(self._archive_name, self.get_lines())
        self.set_modified(False)

class DirExcludesEditView(ExcludesView):
    __g_type_name__ = "DirExcludesEditView"
    BUFFER = DirExcludesEditBuffer

class DirExcludesEditWidget(actions.ClientAndButtonsWidget):
    __g_type_name__ = "DirExcludesEditWidget"
    CLIENT = DirExcludesEditView
    BUTTONS = ["insert_dir_path", "undo_changes", "apply_changes"]
    SCROLLABLE = True

class DirExcludesEditDialog(Gtk.Dialog):
    __g_type_name__ = "DirExcludesEditDialog"
    def __init__(self, archive_name, parent=None):
        title = _("Edit \"{}\" archive\'s directory exclusions.").format(archive_name)
        parent = parent if parent else dialogue.main_window
        Gtk.Dialog.__init__(self, title=title, parent=parent)
        self.new_archive_widget = DirExcludesEditWidget(archive_name=archive_name)
        self.get_content_area().pack_start(self.new_archive_widget, expand=True, fill=True, padding=0)
        self.show_all()

class FileExcludesEditBuffer(DirExcludesEditBuffer):
    __g_type_name__ = "FileExcludesEditBuffer"
    def _load_content(self):
        lines = config.read_exclude_file_lines(self._archive_name)
        if lines:
            self.set_text(os.linesep.join(lines) + os.linesep)
        else:
            self.set_text("")
        self.set_modified(False)
    def _write_content(self):
        config.write_exclude_file_lines(self._archive_name, self.get_lines())
        self.set_modified(False)

class FileExcludesEditView(ExcludesView):
    __g_type_name__ = "FileExcludesEditView"
    BUFFER = FileExcludesEditBuffer

class FileExcludesEditWidget(actions.ClientAndButtonsWidget):
    __g_type_name__ = "FileExcludesEditWidget"
    CLIENT = FileExcludesEditView
    BUTTONS = ["insert_file_path", "undo_changes", "apply_changes"]
    SCROLLABLE = True

class FileExcludesEditDialog(Gtk.Dialog):
    __g_type_name__ = "FileExcludesEditDialog"
    def __init__(self, archive_name, parent=None):
        title = _("Edit \"{}\" archive\'s directory exclusions.").format(archive_name)
        parent = parent if parent else dialogue.main_window
        Gtk.Dialog.__init__(self, title=title, parent=parent)
        self.new_archive_widget = FileExcludesEditWidget(archive_name=archive_name)
        self.get_content_area().pack_start(self.new_archive_widget, expand=True, fill=True, padding=0)
        self.show_all()

class NewArchiveWidget(Gtk.VBox):
    __g_type_name__ = "NewArchiveWidget"
    def __init__(self):
        Gtk.VBox.__init__(self)
        name_label = Gtk.Label()
        name_label.set_markup(_("Name:"))
        self._name = dialogue.ReadTextWidget()
        location_label = Gtk.Label()
        location_label.set_markup(_("Location:"))
        repo_label = Gtk.Label()
        repo_label.set_markup(_("Content Repository:"))
        self._location = dialogue.EnterDirPathWidget()
        self._compress_snapshots = Gtk.CheckButton(_("Compress Snapshots?"))
        self._compress_snapshots.set_active(True)
        self._skip_broken_slinks = Gtk.CheckButton(_("Skip Broken Symbolic Links?"))
        self._skip_broken_slinks.set_active(True)
        self._select_repo = g_repos.RepoComboBox()
        cb_hbox = Gtk.HBox()
        cb_hbox.add(self._compress_snapshots)
        cb_hbox.add(self._skip_broken_slinks)
        grid = Gtk.Grid()
        grid.add(name_label)
        grid.attach_next_to(self._name, name_label, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach_next_to(repo_label, self._name, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach_next_to(self._select_repo, repo_label, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach_next_to(location_label, name_label, Gtk.PositionType.BOTTOM, 1, 1)
        grid.attach_next_to(self._location, location_label, Gtk.PositionType.RIGHT, 3, 1)
        self.pack_start(grid, expand=False, fill=False, padding=0)
        self.pack_start(cb_hbox, expand=False, fill=False, padding=0)
        notebook = Gtk.Notebook()
        self._includes_table = IncludesTable()
        notebook.append_page(self._includes_table, Gtk.Label(_("Included Files and Directories")))
        self._exclude_dirs_text = DirExcludesWidget()
        notebook.append_page(self._exclude_dirs_text, Gtk.Label(_("Exclude Directories Matching")))
        self._exclude_files_text = FileExcludesWidget()
        notebook.append_page(self._exclude_files_text, Gtk.Label(_("Exclude Files Matching")))
        self.pack_start(notebook, expand=True, fill=True, padding=0)
        self.show_all()
    def create_archive(self):
        archive_name = self._name.entry.get_text()
        if not archive_name:
            dialogue.alert_user(_("\"Name\" is a required field."))
            return False
        location_dir_path = self._location.path
        if not location_dir_path:
            dialogue.alert_user(_("\"Location\" is a required field."))
            return False
        try:
            repo_spec = self._select_repo.get_selected_repo_spec()
            if not repo_spec:
                dialogue.alert_user(_("\"Content Repository\" is a required field."))
                return False
        except excpns.UnknownRepository as edata:
            dialogue.report_exception_as_error(edata)
            return False
        includes = self._includes_table.get_included_paths()
        if not len(includes):
            dialogue.alert_user(_("\"Included Files and Directories\" is required."))
            return False
        compress_default = self._compress_snapshots.get_active()
        skip_broken_sl = self._skip_broken_slinks.get_active()
        exclude_dir_globs = self._exclude_dirs_text.get_lines()
        exclude_file_globs = self._exclude_files_text.get_lines()
        try:
            snapshot.create_new_archive(
                archive_name,
                location_dir_path,
                repo_spec,
                includes,
                exclude_dir_globs,
                exclude_file_globs,
                skip_broken_sl,
                compress_default)
            enotify.notify_events(NE_NEW_ARCHIVE)
        except excpns.Error as edata:
            dialogue.report_exception_as_error(edata)
            return False
        return True

class NewArchiveDialog(dialogue.CancelOKDialog):
    __g_type_name__ = "NewArchiveDialog"
    def __init__(self, parent=None):
        dialogue.CancelOKDialog.__init__(self, title=_("Create New Archive"), parent=parent)
        self.new_archive_widget = NewArchiveWidget()
        self.get_content_area().pack_start(self.new_archive_widget, expand=True, fill=True, padding=0)
        self.show_all()

class ArchiveComboBox(gutils.UpdatableComboBoxText, enotify.Listener):
    __g_type_name__ = "ArchiveComboBox"
    RSECTION = "snapshots"
    RONAME = "last_archive_viewed"
    recollect.define(RSECTION, RONAME, recollect.Defn(str, ""))
    def __init__(self):
        gutils.UpdatableComboBoxText.__init__(self)
        enotify.Listener.__init__(self)
        self.add_notification_cb(NE_ARCHIVE_POPN_CHANGE, self._enotify_cb)
        last_archive_name = recollect.get(self.RSECTION, self.RONAME)
        if last_archive_name:
            model = self.get_model()
            model_iter = model.get_iter_first()
            while model_iter is not None:
                row = model.get(model_iter, 0)
                if row[0] == last_archive_name:
                    self.set_active_iter(model_iter)
                    break
                else:
                    model_iter = model.iter_next(model_iter)
            if model_iter is None:
                self.set_active(0)
        self.connect("changed", self._save_last_archive_cb)
    def _save_last_archive_cb(self, combo_box):
        archive_name = combo_box.get_active_text()
        if archive_name:
            recollect.set(self.RSECTION, self.RONAME, archive_name)
        return False
    def _enotify_cb(self, **kwargs):
        self.update_contents()
    def _get_updated_item_list(self):
        return config.get_archive_name_list()
    def get_selected_archive_spec(self):
        archive_name = self.get_active_text()
        if archive_name:
            return config.read_archive_spec(archive_name)
        return None

class ArchivesWidget(Gtk.VBox, actions.CAGandUIManager):
    __g_type_name__ = "ArchivesWidget"
    UI_DESCR = """
    <ui>
        <toolbar name="ArchiveToolBar">
            <toolitem action="create_new_archive"/>
        </toolbar>
    </ui>
    """
    def __init__(self):
        Gtk.VBox.__init__(self)
        actions.CAGandUIManager.__init__(self)
        toolbar = self.ui_manager.get_widget("/ArchiveToolBar")
        self.pack_start(toolbar, expand=False, fill=True, padding=0)
        self._archive_list_view = ArchiveListView()
        self.pack_start(gutils.wrap_in_scrolled_window(self._archive_list_view), expand=True, fill=True, padding=0)
    def populate_action_groups(self):
        pass

def create_new_archive_acb(_action=None):
    dialog = NewArchiveDialog()
    while dialog.run() == Gtk.ResponseType.OK:
        if dialog.new_archive_widget.create_archive():
            break
    dialog.destroy()

actions.CLASS_INDEP_AGS[g_repos.AC_REPOS_AVAILABLE].add_actions(
    [
        ("create_new_archive", icons.STOCK_NEW_ARCHIVE, _("New Archive"), None,
         _("Create a new snapshot archive."),
         create_new_archive_acb
        ),
    ])

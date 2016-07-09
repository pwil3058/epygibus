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

from .. import config
from .. import utils
from .. import excpns
from .. import snapshot

from . import g_repos
from . import actions
from . import enotify
from . import auto_update
from . import table
from . import icons
from . import tlview
from . import dialogue
from . import gutils

AC_ARCHIVES_AVAILABLE = actions.ActionCondns.new_flag()
NE_NEW_ARCHIVE, NE_DELETE_ARCHIVE, NE_NUM_ARCHIVE_CHANGE = enotify.new_event_flags_and_mask(2)

_n_archives = 0

def get_archive_available_condn():
    if _n_archives:
        return actions.MaskedCondns(AC_ARCHIVES_AVAILABLE, AC_ARCHIVES_AVAILABLE)
    else:
        return actions.MaskedCondns(0, AC_ARCHIVES_AVAILABLE)

def _ne_num_archive_change_cb(**kwargs):
    global _n_archives
    old_n_archives = _n_archives
    _n_archives = len(config.get_archive_name_list())
    if old_n_archives != _n_archives:
        actions.CLASS_INDEP_AGS.update_condns(get_archive_available_condn())

_ne_num_archive_change_cb()

enotify.add_notification_cb(NE_NUM_ARCHIVE_CHANGE, _ne_num_archive_change_cb)

def _auto_update_cb(events_so_far, _args):
    if events_so_far & NE_NUM_ARCHIVE_CHANGE or len(config.get_archive_name_list()) == _n_archives:
        return 0
    return NE_NEW_ARCHIVE

auto_update.register_cb(_auto_update_cb)

class IncludesModel(tlview.NamedListStore):
    Row = collections.namedtuple("Row", ["included_path"])
    types = Row(included_path=GObject.TYPE_STRING)

class IncludesView(tlview.View, actions.CBGUserMixin):
    Model = IncludesModel
    specification = tlview.ViewSpec(
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
                            start=True
                        ),
                        properties={"editable" : False},
                        cell_data_function_spec=None,
                        attributes={"text" : Model.col_index("included_path")}
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
                 self._add_file_path_acb),
                ("table_add_dir_path", Gtk.Button.new_with_label(_("Append Directory")),
                 _("Append a new directory path to the includes table"),
                 self._add_dir_path_acb),
            ])
        self.button_groups[actions.AC_SELN_MADE].add_buttons(
            [
                ("table_delete_selection", Gtk.Button.new_from_stock(Gtk.STOCK_DELETE),
                 _("Delete selected row(s)"),
                 self._delete_selection_acb),
                ("table_insert_file_path", Gtk.Button.new_with_label(_("Insert File")),
                 _("Insert a new file path before the selected row(s)"),
                 self._insert_file_path_acb),
                ("table_insert_dir_path", Gtk.Button.new_with_label(_("Insert Directory")),
                 _("Insert a new directory path before the selected row(s)"),
                 self._insert_dir_path_acb),
            ])
    def get_included_paths(self):
        return [row.included_path for row in self.model.named()]
    def _add_file_path_acb(self, _action=None):
        file_path = dialogue.select_file(_("Select File to Add"), absolute=True)
        if file_path:
            self.model.append(self.Model.Row(file_path))
    def _add_dir_path_acb(self, _action=None):
        dir_path = dialogue.select_directory(_("Select Directory to Add"), absolute=True)
        if dir_path:
            self.model.append(self.Model.Row(dir_path))
    def _insert_file_path_acb(self, _action=None):
        file_path = dialogue.select_file(_("Select File to Insert"), absolute=True)
        if file_path:
            tlview.insert_before_selection(self.get_selection(), self.Model.Row(file_path))
    def _insert_dir_path_acb(self, _action=None):
        dir_path = dialogue.select_directory(_("Select Directory to Insert"), absolute=True)
        if dir_path:
            tlview.insert_before_selection(self.get_selection(), self.Model.Row(dir_path))
    def _delete_selection_acb(self, _action=None):
        tlview.delete_selection(self.get_selection())

class IncludesTable(actions.ClientAndButtonsWidget):
    CLIENT = IncludesView
    BUTTONS = ["table_add_dir_path", "table_insert_dir_path", "table_add_file_path", "table_insert_file_path", "table_delete_selection"]
    SCROLLABLE = True
    def get_included_paths(self):
        return self.client.get_included_paths()

class ExcludesView(Gtk.TextView, actions.CBGUserMixin):
    def __init__(self):
        Gtk.TextView.__init__(self)
        actions.CBGUserMixin.__init__(self)
    def populate_button_groups(self):
        self.button_groups[actions.AC_DONT_CARE].add_buttons(
            [
                ("insert_dir_path", Gtk.Button.new_with_label(_("Insert Directory Path")),
                 _("Browse for and insert a directory path at the text cursor."),
                 self._insert_dir_path_acb),
                ("insert_file_path", Gtk.Button.new_with_label(_("Insert File Path")),
                 _("Browse for and insert a file path at the text cursor."),
                 self._insert_file_path_acb),
            ])
    def _insert_dir_path_acb(self, _action=None):
        dir_path = dialogue.select_directory(_("Select Directory to Insert"), absolute=True)
        if dir_path:
            self.get_buffer().insert_at_cursor(dir_path + "\n")
    def _insert_file_path_acb(self, _action=None):
        dir_path = dialogue.select_file(_("Select Directory to Insert"), absolute=True)
        if dir_path:
            self.get_buffer().insert_at_cursor(dir_path + "\n")
    def get_lines(self):
        bfr = self.get_buffer()
        start = bfr.get_start_iter()
        end = bfr.get_end_iter()
        return [line.rstrip() for line in bfr.get_text(start, end, False).splitlines(False)]

class DirExcludesWidget(actions.ClientAndButtonsWidget):
    CLIENT = ExcludesView
    BUTTONS = ["insert_dir_path"]
    SCROLLABLE = True
    def get_lines(self):
        return self.client.get_lines()

class FileExcludesWidget(actions.ClientAndButtonsWidget):
    CLIENT = ExcludesView
    BUTTONS = ["insert_file_path"]
    SCROLLABLE = True
    def get_lines(self):
        return self.client.get_lines()

class NewArchiveWidget(Gtk.VBox):
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
        location_dir_path = self._location.dir_path
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
    def __init__(self, parent=None):
        dialogue.CancelOKDialog.__init__(self, title=_("Create New Archive"), parent=parent)
        self.new_archive_widget = NewArchiveWidget()
        self.get_content_area().pack_start(self.new_archive_widget, expand=True, fill=True, padding=0)
        self.show_all()

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

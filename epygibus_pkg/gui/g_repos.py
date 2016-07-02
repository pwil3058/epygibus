### Copyright (C) 2005-2016 Peter Williams <pwil3058@gmail.com>
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
from .. import repo
from .. import utils
from .. import excpns

from . import actions
from . import enotify
from . import auto_update
from . import table
from . import icons
from . import tlview
from . import dialogue

AC_REPOS_AVAILABLE = actions.ActionCondns.new_flag()
NE_NEW_REPO = enotify.new_event_flag()
NE_REPO_STATS_CHANGE = enotify.new_event_flag()

_n_repos = 0

def get_repo_available_condn():
    if _n_repos:
        return actions.MaskedCondns(AC_REPOS_AVAILABLE, AC_REPOS_AVAILABLE)
    else:
        return actions.MaskedCondns(0, AC_REPOS_AVAILABLE)

def _ne_new_repo_cb(**kwargs):
    global _n_repos
    old_n_repos = _n_repos
    _n_repos = len(config.get_repo_name_list())
    if old_n_repos != _n_repos:
        actions.CLASS_INDEP_AGS.update_condns(get_repo_available_condn())

_ne_new_repo_cb()

enotify.add_notification_cb(NE_NEW_REPO, _ne_new_repo_cb)

def _auto_update_cb(events_so_far, _args):
    if events_so_far & NE_NEW_REPO or len(config.get_repo_name_list()) == _n_repos:
        return 0
    return NE_NEW_REPO

auto_update.register_cb(_auto_update_cb)

class RepoTableData(table.TableData):
    def _get_data_text(self, h):
        repo_spec_list = config.get_repo_spec_list()
        h.update(str(repo_spec_list).encode())
        return repo_spec_list
    def _finalize(self, pdt):
        self._repo_spec_list = pdt
    def iter_rows(self):
        for repo_spec in self._repo_spec_list:
            yield repo_spec

class RepoListView(table.MapManagedTableView):
    class Model(table.MapManagedTableView.Model):
        Row = config.Repo
        types = Row(name=GObject.TYPE_STRING, base_dir_path=GObject.TYPE_STRING, compressed=GObject.TYPE_BOOLEAN,)
        def get_tag_name(self, plist_iter):
            return self.get_value_named(plist_iter, "name")
        def get_base_dir_path(self, plist_iter):
            return self.get_value_named(plist_iter, "base_dir_path")
        def get_compressed(self, plist_iter):
            return self.get_value_named(plist_iter, "compressed")
    PopUp = None
    SET_EVENTS = 0
    REFRESH_EVENTS = NE_NEW_REPO
    AU_REQ_EVENTS = NE_NEW_REPO
    UI_DESCR = ""
    specification = table.simple_text_specification(Model, (_("Name"), "name", 0.0), (_("Location"), "base_dir_path", 0.0), (_("Compressed?"), "compressed", 0.0),)
    def __init__(self, busy_indicator=None, size_req=None):
        table.MapManagedTableView.__init__(self, busy_indicator=busy_indicator, size_req=size_req)
        self.set_contents()
    def get_selected_repo(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_tag_name(store_iter)
    def _get_table_db(self):
        return RepoTableData()

class RepoListWidget(table.TableWidget):
    View = RepoListView

class RepoStatsRow(collections.namedtuple("RepoSt", ["references", "referenced_items", "referenced_content_bytes", "referenced_stored_bytes", "unreferenced_items", "unreferenced_content_bytes", "unreferenced_stored_bytes"])):
    @property
    def total_items(self):
        return self.total_referenced_items + self.total_unreferenced_items
    @property
    def total_content_bytes(self):
        return self.total_referenced_content_bytes + self.total_unreferenced_content_bytes
    @property
    def total_stored_bytes(self):
        return self.total_referenced_stored_bytes + self.total_unreferenced_stored_bytes

RSRow = collections.namedtuple("RSRow", ["name", "nitems", "content_bytes", "stored_bytes", "references", "referenced_items", "referenced_content_bytes", "referenced_stored_bytes", "unreferenced_items", "unreferenced_content_bytes", "unreferenced_stored_bytes"])

NUM_FT = "{:,}"

class RepoStatsTableData(table.TableData):
    def _get_data_text(self, h):
        repo_stats_list = repo.get_repo_storage_stats_list()
        h.update(str(repo_stats_list).encode())
        return repo_stats_list
    def _finalize(self, pdt):
        self._repo_stats_list = pdt
    def iter_rows(self):
        for repo_name, repo_stats in self._repo_stats_list:
            nitems = NUM_FT.format(repo_stats.total_items)
            content_bytes = utils.format_bytes(repo_stats.total_content_bytes)
            stored_bytes = utils.format_bytes(repo_stats.total_stored_bytes)
            references = NUM_FT.format(repo_stats.references)
            referenced_items = NUM_FT.format(repo_stats.referenced_items)
            referenced_content_bytes = utils.format_bytes(repo_stats.referenced_content_bytes)
            referenced_stored_bytes = utils.format_bytes(repo_stats.referenced_stored_bytes)
            unreferenced_items = NUM_FT.format(repo_stats.unreferenced_items)
            unreferenced_content_bytes = utils.format_bytes(repo_stats.unreferenced_content_bytes)
            unreferenced_stored_bytes = utils.format_bytes(repo_stats.unreferenced_stored_bytes)
            yield RSRow(repo_name, nitems, content_bytes, stored_bytes, references, referenced_items, referenced_content_bytes, referenced_stored_bytes, unreferenced_items, unreferenced_content_bytes, unreferenced_stored_bytes)

class RepoStatsListView(table.MapManagedTableView):
    class Model(table.MapManagedTableView.Model):
        Row = RSRow
        types = Row(name=GObject.TYPE_STRING,
                    nitems=GObject.TYPE_STRING,
                    content_bytes=GObject.TYPE_STRING,
                    stored_bytes=GObject.TYPE_STRING,
                    references=GObject.TYPE_STRING,
                    referenced_items=GObject.TYPE_STRING,
                    referenced_content_bytes=GObject.TYPE_STRING,
                    referenced_stored_bytes=GObject.TYPE_STRING,
                    unreferenced_items=GObject.TYPE_STRING,
                    unreferenced_content_bytes=GObject.TYPE_STRING,
                    unreferenced_stored_bytes=GObject.TYPE_STRING)
    PopUp = "/repos_popup"
    SET_EVENTS = 0
    REFRESH_EVENTS = NE_REPO_STATS_CHANGE | NE_NEW_REPO
    AU_REQ_EVENTS = NE_REPO_STATS_CHANGE
    UI_DESCR = """
    <ui>
      <popup name="repos_STATS_popup">
        <menuitem action="show_selected_repo_spec"/>
        <separator/>
      </popup>
    </ui>
    """
    #hdrs_and_flds = (
    specification = table.simple_text_specification(Model,
        (_("Name"), "name", 0.0),
        (_("#Items"), "nitems", 1.0),
        (_("Content"), "content_bytes", 1.0),
        (_("Stored"), "stored_bytes", 1.0),
        (_("References"), "references", 1.0),
        (_("#Referenced"), "referenced_items", 1.0),
        (_("Content"), "referenced_content_bytes", 1.0),
        (_("Stored"), "referenced_stored_bytes", 1.0),
        (_("#Unreferenced"), "unreferenced_items", 1.0),
        (_("Content"), "unreferenced_content_bytes", 1.0),
        (_("Stored"), "unreferenced_stored_bytes", 1.0),
    )
    def __init__(self, busy_indicator=None, size_req=None):
        table.MapManagedTableView.__init__(self, busy_indicator=busy_indicator, size_req=size_req)
        self.set_contents()
    def populate_action_groups(self):
        table.MapManagedTableView.populate_action_groups(self)
        self.action_groups[actions.AC_SELN_UNIQUE].add_actions(
            [
                ("show_selected_repo_spec", icons.STOCK_REPO_SHOW, _("Show"), None,
                  _("Show the specification of the selected repo."),
                  lambda _action=None: None #RepoDiffDialog(repo=self.get_selected_repo()).show()
                ),
            ])
    def get_selected_repo(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_tag_name(store_iter)
    def _get_table_db(self):
        return RepoStatsTableData()

class RepoStatsListWidget(table.TableWidget):
    View = RepoStatsListView

class NewRepoWidget(Gtk.VBox):
    def __init__(self):
        Gtk.VBox.__init__(self)
        name_label = Gtk.Label()
        name_label.set_markup(_("Name:"))
        self._name = dialogue.ReadTextWidget()
        location_label = Gtk.Label()
        location_label.set_markup(_("Location:"))
        self._location = dialogue.EnterDirPathWidget()
        self._compress_content = Gtk.CheckButton(_("Compress Stored Content?"))
        self._compress_content.set_active(True)
        grid = Gtk.Grid()
        grid.add(name_label)
        grid.attach_next_to(self._name, name_label, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach_next_to(location_label, name_label, Gtk.PositionType.BOTTOM, 1, 1)
        grid.attach_next_to(self._location, location_label, Gtk.PositionType.RIGHT, 1, 1)
        self.pack_start(grid, expand=False, fill=False, padding=0)
        self.pack_start(self._compress_content, expand=False, fill=False, padding=0)
        self.show_all()
    def create_repo(self):
        name = self._name.entry.get_text()
        if not name:
            dialogue.alert_user(_("\"Name\" is a required field."))
            return False
        location = self._location.dir_path
        if not location:
            dialogue.alert_user(_("\"Location\" is a required field."))
            return False
        compress = self._compress_content.get_active()
        try:
            repo.create_new_repo(name, location, compress)
        except excpns.Error as edata:
            dialogue.report_exception_as_error(edata)
            return False
        return True

class NewRepoDialog(dialogue.CancelOKDialog):
    def __init__(self, parent=None):
        dialogue.CancelOKDialog.__init__(self, title=_("Create New Repo"), parent=parent)
        self.new_repo_widget = NewRepoWidget()
        self.get_content_area().add(self.new_repo_widget)
        self.show_all()

def create_new_repo_acb(_action=None):
    dialog = NewRepoDialog()
    while dialog.run() == Gtk.ResponseType.OK:
        if dialog.new_repo_widget.create_repo():
            break
    dialog.destroy()

actions.CLASS_INDEP_AGS[actions.AC_DONT_CARE].add_actions(
    [
        ("create_new_repo", icons.STOCK_NEW_REPO, _("New Repo"), None,
         _("Create a new content repository."),
         create_new_repo_acb
        ),
    ])

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
from gi.repository import Pango

from .. import config
from .. import repo
from .. import utils

from . import actions
from . import table
from . import icons
from . import tlview

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
    REFRESH_EVENTS = 0
    AU_REQ_EVENTS = 0
    UI_DESCR = ""
    specification = table.simple_text_specification(Model, (_("Name"), "name"), (_("Location"), "base_dir_path"), (_("Compressed?"), "compressed"),)
    def __init__(self, busy_indicator=None, size_req=None):
        table.MapManagedTableView.__init__(self, busy_indicator=busy_indicator, size_req=size_req)
        self.set_contents()
    def get_selected_repo(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_tag_name(store_iter)
    def _get_table_db(self):
        return RepoTableData()


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
    REFRESH_EVENTS = 0
    AU_REQ_EVENTS = 0
    UI_DESCR = """
    <ui>
      <popup name="repos_STATS_popup">
        <menuitem action="show_selected_repo_spec"/>
        <separator/>
      </popup>
    </ui>
    """
    hdrs_and_flds = (
        (_("Name"), "name", Pango.Alignment.LEFT, 0.0),
        (_("#Items"), "nitems", Pango.Alignment.RIGHT, 1.0),
        (_("Content"), "content_bytes", Pango.Alignment.RIGHT, 1.0),
        (_("Stored"), "stored_bytes", Pango.Alignment.RIGHT, 1.0),
        (_("References"), "references", Pango.Alignment.RIGHT, 1.0),
        (_("#Referenced"), "referenced_items", Pango.Alignment.RIGHT, 1.0),
        (_("Content"), "referenced_content_bytes", Pango.Alignment.RIGHT, 1.0),
        (_("#Unreferenced"), "unreferenced_items", Pango.Alignment.RIGHT, 1.0),
        (_("Contents"), "unreferenced_content_bytes", Pango.Alignment.RIGHT, 1.0),
        (_("Stored"), "unreferenced_stored_bytes", Pango.Alignment.RIGHT, 1.0),)
    specification = tlview.ViewSpec(
        properties={
            "enable-grid-lines" : False,
            "reorderable" : False,
            "rules_hint" : False,
            "headers-visible" : True,
        },
        selection_mode=Gtk.SelectionMode.SINGLE,
        columns=[tlview.simple_column(hdr, tlview.fixed_text_cell(Model, fld, align, xalign)) for hdr, fld, align, xalign in hdrs_and_flds]
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

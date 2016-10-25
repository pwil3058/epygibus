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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject

from .. import config
from .. import repo
from .. import utils
from .. import excpns
from ..bab import enotify

from . import actions
from . import auto_update
from . import table
from . import icons
from . import tlview
from . import dialogue
from . import gutils

AC_REPOS_AVAILABLE = actions.ActionCondns.new_flag()
NE_NEW_REPO, NE_DELETE_REPO, NE_REPO_POPN_CHANGE = enotify.new_event_flags_and_mask(2)
NE_REPO_STATS_CHANGE = enotify.new_event_flag()
NE_REPO_SPEC_CHANGE = enotify.new_event_flag()

_n_repos = 0
_repo_name_hash_digest = None

def get_repo_name_hash_digest_etc():
    import hashlib
    repo_name_list = config.get_repo_name_list()
    return (hashlib.sha1(str(repo_name_list).encode()).digest(), len(repo_name_list),)

def get_repo_available_condn():
    if _n_repos:
        return actions.MaskedCondns(AC_REPOS_AVAILABLE, AC_REPOS_AVAILABLE)
    else:
        return actions.MaskedCondns(0, AC_REPOS_AVAILABLE)

def _ne_num_repo_change_cb(**kwargs):
    global _n_repos
    old_n_repos = _n_repos
    global _repo_name_hash_digest
    old_repo_name_hash_digest = _repo_name_hash_digest
    _repo_name_hash_digest, _n_repos = get_repo_name_hash_digest_etc()
    if old_n_repos != _n_repos and not (old_n_repos and _n_repos):
        actions.CLASS_INDEP_AGS.update_condns(get_repo_available_condn())

_ne_num_repo_change_cb()

enotify.add_notification_cb(NE_REPO_POPN_CHANGE, _ne_num_repo_change_cb)

def _auto_update_cb(events_so_far, _args):
    if events_so_far & NE_REPO_POPN_CHANGE or get_repo_name_hash_digest_etc()[0] == _repo_name_hash_digest:
        return 0
    return NE_NEW_REPO

auto_update.register_cb(_auto_update_cb)

class RepoTableData(table.TableData):
    __g_type_name__ = "RepoTableData"
    def _get_data_text(self, h):
        repo_spec_list = config.get_repo_spec_list()
        h.update(str(repo_spec_list).encode())
        return repo_spec_list
    def _finalize(self, pdt):
        self._repo_spec_list = pdt
    def iter_rows(self):
        for repo_spec in sorted(self._repo_spec_list):
            yield repo_spec

class RepoListModel(table.MapManagedTableView.MODEL):
    __g_type_name__ = "RepoListModel"
    ROW = config.Repo
    TYPES = ROW(name=GObject.TYPE_STRING, base_dir_path=GObject.TYPE_STRING, compressed=GObject.TYPE_BOOLEAN,)

def _repo_list_spec():
    specification = tlview.ViewSpec(
        properties={
            "enable-grid-lines" : False,
            "reorderable" : False,
            "rules_hint" : False,
            "headers-visible" : True,
        },
        selection_mode=Gtk.SelectionMode.SINGLE,
        columns=[
            tlview.simple_column(_("Name"), tlview.fixed_text_cell(RepoListModel, "name", 0.0)),
            tlview.simple_column(_("Compressed?"), tlview.fixed_toggle_cell(RepoListModel, "compressed", 0.0)),
            tlview.simple_column(_("Location"), tlview.fixed_text_cell(RepoListModel, "base_dir_path", 0.0)),
        ]
    )
    return specification

class RepoListView(table.MapManagedTableView):
    __g_type_name__ = "RepoListView"
    MODEL = RepoListModel
    PopUp = None
    SET_EVENTS = 0
    REFRESH_EVENTS = NE_REPO_POPN_CHANGE | NE_REPO_SPEC_CHANGE
    AU_REQ_EVENTS = NE_REPO_SPEC_CHANGE
    UI_DESCR = ""
    SPECIFICATION = _repo_list_spec()
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        self.set_contents()
    def get_selected_repo(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_value_named(plist_iter, "name")
    def _get_table_db(self):
        return RepoTableData()

class RepoListWidget(table.TableWidget):
    __g_type_name__ = "RepoListWidget"
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
        for repo_name, repo_stats in sorted(self._repo_stats_list):
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
    __g_type_name__ = "RepoStatsListView"
    class MODEL(tlview.NamedListStore):
        ROW = RSRow
        TYPES = ROW(name=GObject.TYPE_STRING,
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
    PopUp = "/repos_STATS_popup"
    SET_EVENTS = 0
    REFRESH_EVENTS = NE_REPO_STATS_CHANGE | NE_REPO_POPN_CHANGE
    AU_REQ_EVENTS = NE_REPO_STATS_CHANGE
    UI_DESCR = """
    <ui>
      <popup name="repos_STATS_popup">
        <menuitem action="prune_selected_repo"/>
        <menuitem action="show_selected_repo_spec"/>
        <menuitem action="delete_selected_repo"/>
        <separator/>
      </popup>
    </ui>
    """
    SPECIFICATION = table.simple_text_specification(MODEL,
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
    def __init__(self, size_req=None):
        table.MapManagedTableView.__init__(self, size_req=size_req)
        self.set_contents()
    def populate_action_groups(self):
        self.action_groups[actions.AC_SELN_UNIQUE].add_actions(
            [
                ("show_selected_repo_spec", icons.STOCK_REPO_SHOW, _("Show"), None,
                  _("Show the specification of the selected repo."),
                  lambda _action=None: None
                ),
                ("delete_selected_repo", icons.STOCK_REPO_DELETE, _("Delete"), None,
                  _("Delete the selected repository."),
                  lambda _action=None: do_delete_repo(self.get_selected_repo_name())
                ),
                ("prune_selected_repo", icons.STOCK_REPO_PRUNE, _("Prune"), None,
                  _("Delete the selected repository."),
                  lambda _action=None: RepoPruneDialog(self.get_selected_repo_name()).prune()
                ),
            ])
    def get_selected_repo_name(self):
        store, store_iter = self.get_selection().get_selected()
        return None if store_iter is None else store.get_value_named(store_iter, "name")
    def _get_table_db(self):
        return RepoStatsTableData()

class RepoStatsListWidget(table.TableWidget):
    __g_type_name__ = "RepoStatsListWidget"
    View = RepoStatsListView

class NewRepoWidget(Gtk.VBox):
    __g_type_name__ = "NewRepoWidget"
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
        location = self._location.path
        if not location:
            dialogue.alert_user(_("\"Location\" is a required field."))
            return False
        compress = self._compress_content.get_active()
        try:
            repo.create_new_repo(name, location, compress)
            enotify.notify_events(NE_NEW_REPO)
        except excpns.Error as edata:
            dialogue.report_exception_as_error(edata)
            return False
        return True

class NewRepoDialog(dialogue.CancelOKDialog):
    __g_type_name__ = "NewRepoDialog"
    def __init__(self, parent=None):
        dialogue.CancelOKDialog.__init__(self, title=_("Create New Repo"), parent=parent)
        self.new_repo_widget = NewRepoWidget()
        self.get_content_area().add(self.new_repo_widget)
        self.show_all()

class RepoComboBox(gutils.UpdatableComboBoxText, enotify.Listener):
    __g_type_name__ = "RepoComboBox"
    def __init__(self):
        gutils.UpdatableComboBoxText.__init__(self)
        enotify.Listener.__init__(self)
        self.add_notification_cb(NE_REPO_POPN_CHANGE, self._enotify_cb)
    def _enotify_cb(self, **kwargs):
        self.update_contents()
    def _get_updated_item_list(self):
        return config.get_repo_name_list()
    def get_selected_repo_spec(self):
        repo_name = self.get_active_text()
        if repo_name:
            return config.read_repo_spec(repo_name)
        return None

class RepoPruneDialog(Gtk.Dialog):
    def __init__(self, repo_name, parent=None):
        title = _("Pruning: \"{}\".").format(repo_name)
        self._repo_name = repo_name
        parent = parent if parent else dialogue.main_window
        Gtk.Dialog.__init__(self, title, parent, 0, (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        self.set_response_sensitive(Gtk.ResponseType.CLOSE, False)
        self.connect("response", lambda _dialog, _response: self.destroy())
        vbox = Gtk.VBox()
        vbox.pack_start(Gtk.Label(title), expand=False, fill=True, padding=0)
        self._progress_indicator = gutils.ProgressThingy()
        vbox.pack_start(self._progress_indicator, expand=False, fill=True, padding=0)
        self._message = Gtk.Entry()
        self._message.set_editable(False)
        vbox.pack_start(self._message, expand=False, fill=True, padding=0)
        self.get_content_area().add(vbox)
        self.show_all()
    def prune(self):
        self.show()
        repo_mgmt_key = repo.get_repo_mgmt_key(self._repo_name)
        with repo.open_repo_mgr(repo_mgmt_key, writeable=True) as repo_mgr:
            stats = repo_mgr.prune_unreferenced_content(progress_indicator=self._progress_indicator)
        if not stats[0]:
            self._message.set_text(_("Nothing to do."))
        else:
            self._message.set_text(_("{:>4,} unreferenced content items removed freeing {} of content and {} of storage.").format(stats[0], utils.format_bytes(stats[1]), utils.format_bytes(stats[2])))
        self.set_response_sensitive(Gtk.ResponseType.CLOSE, True)


class ReposWidget(Gtk.VBox, actions.CAGandUIManager):
    __g_type_name__ = "ReposWidget"
    UI_DESCR = """
    <ui>
        <toolbar name="RepoToolBar">
            <toolitem action="create_new_repo"/>
        </toolbar>
    </ui>
    """
    def __init__(self):
        Gtk.VBox.__init__(self)
        actions.CAGandUIManager.__init__(self)
        toolbar = self.ui_manager.get_widget("/RepoToolBar")
        self.pack_start(toolbar, expand=False, fill=True, padding=0)
        notebook = Gtk.Notebook()
        self._repo_specs_view = RepoListView()
        notebook.append_page(gutils.wrap_in_scrolled_window(self._repo_specs_view), Gtk.Label(_("Repository Specifications")))
        self._repo_stats_view = RepoStatsListView()
        notebook.append_page(gutils.wrap_in_scrolled_window(self._repo_stats_view), Gtk.Label(_("Repository Statistics")))
        self.pack_start(notebook, expand=True, fill=True, padding=0)
    def populate_action_groups(self):
        pass

def do_delete_repo(repo_name):
    try:
        repo.delete_repo(repo_name)
        enotify.notify_events(NE_DELETE_REPO)
    except Exception as edata:
        dialogue.report_exception_as_error(edata)

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

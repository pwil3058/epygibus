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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from . import actions
from . import enotify
from . import auto_update
from . import g_repos
from . import icons
from . import dialogue

class MainWindow(Gtk.Window, actions.CAGandUIManager, enotify.Listener, dialogue.BusyIndicator):
    UI_DESCR = """
    <ui>
        <toolbar name="RepoToolBar">
            <toolitem action="create_new_repo"/>
        </toolbar>
    </ui>
    """
    def __init__(self):
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        actions.CAGandUIManager.__init__(self)
        enotify.Listener.__init__(self)
        dialogue.BusyIndicator.__init__(self)
        dialogue.init(self)
        self.set_icon_from_file(icons.APP_ICON_FILE)
        self.connect("delete_event", Gtk.main_quit)
        vbox = Gtk.VBox()
        label = Gtk.Label()
        label.set_label("Work in progress.  Try again later.")
        vbox.pack_start(label, expand=False, fill=True, padding=0)
        vbox.pack_start(g_repos.RepoListView(), expand=False, fill=True, padding=0)
        vbox.pack_start(g_repos.RepoStatsListWidget(), expand=True, fill=True, padding=0)
        rcb = g_repos.RepoComboBox()
        rcb.set_active_text("gabba")
        rcb.connect("changed", self._rcb_changed_cb)
        vbox.pack_start(rcb, expand=False, fill=True, padding=0)
        toolbar = self.ui_manager.get_widget("/RepoToolBar")
        vbox.pack_start(toolbar, expand=False, fill=True, padding=0)
        self.add(vbox)
        self.show_all()
    def populate_action_groups(self):
        pass
    def _rcb_changed_cb(self, rcb):
        print("repo:", rcb.get_active_text())

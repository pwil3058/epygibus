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
from . import g_archives
from . import g_snapshots
from . import icons
from . import dialogue

class MainWindow(Gtk.Window, actions.CAGandUIManager, enotify.Listener, dialogue.BusyIndicator):
    UI_DESCR = """
    <ui>
        <menubar name="epygibus_left_menubar">
            <menu action="snapshot_exigency_menu">
              <menuitem action="exig_open_snapshot_file"/>
            </menu>
        </menubar>
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
        lmenu_bar = self.ui_manager.get_widget('/epygibus_left_menubar')
        vbox.pack_start(lmenu_bar, expand=False, fill=True, padding=0)
        notebook = Gtk.Notebook()
        notebook.set_show_border(True)
        notebook.append_page(g_repos.ReposWidget(), Gtk.Label(_("Content Repositories")))
        notebook.append_page(g_archives.ArchivesWidget(), Gtk.Label(_("Snapshot Archives")))
        vbox.pack_start(notebook, expand=True, fill=True, padding=0)
        self.add(vbox)
        self.show_all()
    def populate_action_groups(self):
        pass

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
    __g_type_name__ = "MainWindow"
    UI_DESCR = """
    <ui>
        <menubar name="epygibus_left_menubar">
            <menu action="main_window_file_menu">
              <menuitem action="main_window_quit"/>
            </menu>
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
        self.set_default_icon(icons.APP_ICON_PIXBUF)
        self.set_icon(icons.APP_ICON_PIXBUF)
        self.connect("delete_event", Gtk.main_quit)
        vbox = Gtk.VBox()
        lmenu_bar = self.ui_manager.get_widget('/epygibus_left_menubar')
        vbox.pack_start(lmenu_bar, expand=False, fill=True, padding=0)
        stack = Gtk.Stack()
        stack.add_titled(g_snapshots.SnapshotsMgrWidget(), "snapshots_mgr", _("Snapshots"))
        stack.add_titled(g_archives.ArchivesWidget(), "archive_stats", _("Snapshot Archives"))
        stack.add_titled(g_repos.ReposWidget(), "repo_stats", _("Content Repositories"))
        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        vbox.pack_start(stack_switcher, expand=False, fill=True, padding=0)
        vbox.pack_start(stack, expand=True, fill=True, padding=0)
        self.add(vbox)
        self.show_all()
    def populate_action_groups(self):
        pass

actions.CLASS_INDEP_AGS[actions.AC_DONT_CARE].add_actions(
    [
        ("main_window_file_menu", None, _("File"), ),
        ("main_window_quit", Gtk.STOCK_QUIT, _("Quit"), None,
         _("Close the application."),
         lambda _action: Gtk.main_quit()
        ),
    ])

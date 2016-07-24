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
from gi.repository import Gdk

CSS = b"""
    GtkNotebook tab {
        background-color: shade(@bg_color, 1.22);
        border-color: white;
        border-width: 1px 1px 0 1px;
        border-style: solid;
        box-shadow: none;
    }
    GtkNotebook tab:active {
        border-color: shade(cyan, 0.8);
        border-style: solid;
        border-width: 4px 1px 0 1px;
        background-color: white;
        background-image: none;
        color: @fg_color;
    }
"""

cssprovider = Gtk.CssProvider()
cssprovider.load_from_data(CSS)
screen = Gdk.Screen.get_default()
stylecontext = Gtk.StyleContext()
stylecontext.add_provider_for_screen(screen, cssprovider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

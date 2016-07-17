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
from gi.repository import Gdk

CSS = b"""
    GtkNotebook tab {
        background-color: white;
        border-style: solid;
        border-image: -gtk-gradient (linear, left top, left bottom,
                                    from (alpha (shade (@bg_color, 0.9), 0.0)),
                                    to (shade (@bg_color, 0.9))) 1;
        border-image-width: 0 1px;
        border-color: transparent;
        border-width: 0;
        box-shadow: none;
    }
    GtkNotebook tab:active {
        border-color: shade(@bg_color, 0.82);
        border-style: solid;
        border-width: 1px;
        background-color: shade(@bg_color, 1.02);
        background-image: none;
        color: @fg_color;
    }
"""

cssprovider = Gtk.CssProvider()
cssprovider.load_from_data(CSS)
screen = Gdk.Screen.get_default()
stylecontext = Gtk.StyleContext()
stylecontext.add_provider_for_screen(screen, cssprovider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

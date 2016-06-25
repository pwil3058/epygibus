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

import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject

main_window = None

def show_busy():
    if main_window is not None:
        main_window.show_busy()

def unshow_busy():
    if main_window is not None:
        main_window.unshow_busy()

def is_busy():
    return main_window is None or main_window.is_busy

def init(window):
    global main_window
    main_window = window

class BusyIndicator:
    def __init__(self, parent=None):
        self.parent_indicator = parent
        self._count = 0
    def show_busy(self):
        if self.parent:
            self.parent.show_busy()
        self._count += 1
        if self._count == 1 and self.window:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            while gtk.events_pending():
                gtk.main_iteration()
    def unshow_busy(self):
        if self.parent:
            self.parent.unshow_busy()
        self._count -= 1
        assert self._count >= 0
        if self._count == 0 and self.window:
            self.window.set_cursor(None)
    @property
    def is_busy(self):
        return self._count > 0

class BusyIndicatorUser(object):
    def __init__(self, busy_indicator=None):
        self._busy_indicator = busy_indicator
    def show_busy(self):
        if self._busy_indicator is not None:
            self._busy_indicator.show_busy()
        else:
            show_busy()
    def unshow_busy(self):
        if self._busy_indicator is not None:
            self._busy_indicator.unshow_busy()
        else:
            unshow_busy()
    def set_busy_indicator(self, busy_indicator=None):
        self._busy_indicator = busy_indicator

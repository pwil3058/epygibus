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

class TimeOutController(object):
    ToggleData = collections.namedtuple('ToggleData', ['name', 'label', 'tooltip', 'stock_id'])
    def __init__(self, toggle_data, function=None, is_on=True, interval=10000):
        self._interval = abs(interval)
        self._timeout_id = None
        self._function = function
        self.toggle_action = Gtk.ToggleAction(
                toggle_data.name, toggle_data.label,
                toggle_data.tooltip, toggle_data.stock_id
            )
        # TODO: find out how to do this in PyGTK3
        #self.toggle_action.set_menu_item_type(Gtk.CheckMenuItem)
        #self.toggle_action.set_tool_item_type(Gtk.ToggleToolButton)
        self.toggle_action.connect("toggled", self._toggle_acb)
        self.toggle_action.set_active(is_on)
    def _toggle_acb(self, _action=None):
        if self.toggle_action.get_active():
            self._restart_cycle()
        else:
            self._stop_cycle()
    def _timeout_cb(self):
        if self._function:
            self._function()
        return self.toggle_action.get_active()
    def _stop_cycle(self):
        if self._timeout_id:
            GObject.source_remove(self._timeout_id)
            self._timeout_id = None
    def _restart_cycle(self):
        self._stop_cycle()
        self._timeout_id = GObject.timeout_add(self._interval, self._timeout_cb)
    def set_function(self, function):
        self._stop_cycle()
        self._function = function
        self._toggle_acb()
    def set_interval(self, interval):
        if interval > 0 and interval != self._interval:
            self._interval = interval
            self._toggle_acb()
    def get_interval(self):
        return self._interval

class MappedManager(object):
    def __init__(self):
        self.is_mapped = False
        self.connect("map", self._map_cb)
        self.connect("unmap", self._unmap_cb)
    def _map_cb(self, widget=None):
        self.is_mapped = True
        self.map_action()
    def _unmap_cb(self, widget=None):
        self.is_mapped = False
        self.unmap_action()
    def map_action(self):
        pass
    def unmap_action(self):
        pass

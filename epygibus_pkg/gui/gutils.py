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

class FramedScrollWindow(Gtk.Frame):
    def __init__(self, policy=(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)):
        Gtk.Frame.__init__(self)
        self._sw = Gtk.ScrolledWindow()
        Gtk.Frame.add(self, self._sw)
    def add(self, widget):
        self._sw.add(widget)
    def set_policy(self, hpolicy, vpolicy):
        return self._sw.set_policy(hpolicy, vpolicy)
    def get_hscrollbar(self):
        return self._sw.get_hscrollbar()
    def get_vscrollbar(self):
        return self._sw.get_hscrollbar()

def wrap_in_scrolled_window(widget, policy=(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC), with_frame=True, label=None):
    scrw = FramedScrollWindow(label) if with_frame else Gtk.ScrolledWindow()
    scrw.set_policy(policy[0], policy[1])
    scrw.add(widget)
    scrw.show_all()
    return scrw

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

class SplitBar(Gtk.HBox):
    def __init__(self, expand_lhs=True, expand_rhs=False):
        Gtk.HBox.__init__(self)
        self.lhs = Gtk.HBox()
        self.pack_start(self.lhs, expand=expand_lhs, fill=True, padding=0)
        self.rhs = Gtk.HBox()
        self.pack_end(self.rhs, expand=expand_rhs, fill=True, padding=0)

class UpdatableComboBoxText(Gtk.ComboBoxText):
    def __init__(self):
        Gtk.ComboBoxText.__init__(self)
        self.update_contents()
        self.show_all()
    def remove_text_item(self, item):
        model = self.get_model()
        for index in range(len(model)):
            if model[index][0] == item:
                self.remove(index)
                return True
        return False
    def insert_text_item(self, item):
        model = self.get_model()
        if len(model) == 0 or model[-1][0] < item:
            self.append_text(item)
            return len(model) - 1
        index = 0
        while index < len(model) and model[index][0] < item:
            index += 1
        self.insert_text(index, item)
        return index
    def set_active_text(self, item):
        model = self.get_model()
        index = 0
        while index < len(model) and model[index][0] != item:
            index += 1
        self.set_active(index)
    def update_contents(self):
        updated_set = set(self._get_updated_item_list())
        for gone_away in (set([row[0] for row in self.get_model()]) - updated_set):
            self.remove_text_item(gone_away)
        for new_item in (updated_set - set([row[0] for row in self.get_model()])):
            self.insert_text_item(new_item)
    def _get_updated_item_list(self):
        assert False, "_get_updated_item_list() must be defined in child"

def yield_to_pending_events():
    while True:
        Gtk.main_iteration()
        if not Gtk.events_pending():
            break

class ProgessThingy(Gtk.ProgressBar):
    def set_expected_total(self, total):
        nsteps = min(100, max(total, 1))
        self._numerator = 0.0
        self._denominator = max(float(total), 1.0)
        self._step = self._denominator / float(nsteps)
        self._next_kick = self._step
        self.set_fraction(0.0)
    def increment_count(self, by=1):
        self._numerator += by
        if self._numerator > self._next_kick:
            self.set_fraction(min(self._numerator / self._denominator, 1.0))
            self._next_kick += self._step
            yield_to_pending_events()
    def finished(self):
        self.set_fraction(1.0)

class PretendWOFile(Gtk.ScrolledWindow):
    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self._view = Gtk.TextView()
        self.add(self._view)
        self.show_all()
    def write(self, text):
        bufr = self._view.get_buffer()
        bufr.insert(bufr.get_end_iter(), text)
    def write_lines(self, lines):
        # take advantage of default "insert-text" handler's updating the iterator
        bufr = self._view.get_buffer()
        bufr_iter = bufr.get_end_iter()
        for line in lines:
            bufr.insert(bufr_iter, line)

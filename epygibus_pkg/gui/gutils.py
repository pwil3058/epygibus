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

import collections

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gio

class FramedScrollWindow(Gtk.Frame):
    __g_type_name__ = "FramedScrollWindow"
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

class TimeOutController:
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

class MappedManager:
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
    __g_type_name__ = "SplitBar"
    def __init__(self, expand_lhs=True, expand_rhs=False):
        Gtk.HBox.__init__(self)
        self.lhs = Gtk.HBox()
        self.pack_start(self.lhs, expand=expand_lhs, fill=True, padding=0)
        self.rhs = Gtk.HBox()
        self.pack_end(self.rhs, expand=expand_rhs, fill=True, padding=0)

class UpdatableComboBoxText(Gtk.ComboBoxText):
    __g_type_name__ = "UpdatableComboBoxText"
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

class ProgressThingy(Gtk.ProgressBar):
    __g_type_name__ = "ProgressThingy"
    def set_expected_total(self, total):
        nsteps = min(100, max(total, 1))
        self._numerator = 0.0
        self._denominator = max(float(total), 1.0)
        self._step = self._denominator / float(nsteps)
        self._next_kick = self._step
        self.set_fraction(0.0)
    def increment_count(self, by=1):
        self._numerator += by
        if self._numerator >= self._next_kick:
            self.set_fraction(min(self._numerator / self._denominator, 1.0))
            self._next_kick += self._step
            yield_to_pending_events()
    def finished(self):
        self.set_fraction(1.0)

class PretendWOFile(Gtk.ScrolledWindow):
    __g_type_name__ = "PretendWOFile"
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

class NotebookWithDelete(Gtk.Notebook):
    __g_type_name__ = "NotebookWithDelete"
    def __init__(self, tab_delete_tooltip=_("Delete this page."), **kwargs):
        self._tab_delete_tooltip = tab_delete_tooltip
        Gtk.Notebook.__init__(self, **kwargs)
    def append_deletable_page(self, page, tab_label):
        label_widget = self._make_label_widget(page, tab_label)
        return self.append_page(page, label_widget)
    def append_deletable_page_menu(self, page, tab_label, menu_label):
        tab_label_widget = self._make_label_widget(page, tab_label)
        return self.append_page_menu(page, tab_label_widget, menu_label)
    def _make_label_widget(self, page, tab_label):
        hbox = Gtk.HBox()
        hbox.pack_start(tab_label, expand=True, fill=True, padding=0)
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_focus_on_click(False)
        icon = Gio.ThemedIcon.new_with_default_fallbacks('window-close-symbolic')
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.MENU)
        image.set_tooltip_text(self._tab_delete_tooltip)
        button.add(image)
        button.set_name("notebook-tab-delete-button")
        hbox.pack_start(button, expand=False, fill=True, padding=0)
        button.connect("clicked", lambda _button: self._delete_page(page))
        hbox.show_all()
        return hbox
    def _prepare_for_delete(self, page):
        pass
    def _delete_page(self, page):
        self._prepare_for_delete(page)
        self.remove_page(self.page_num(page))
    def iterate_pages(self):
        for pnum in range(self.get_n_pages()):
            yield (pnum, self.get_nth_page(pnum))

class YesNoWidget(Gtk.HBox):
    def __init__(self, question_text):
        Gtk.HBox.__init__(self)
        q_label = Gtk.Label(question_text)
        self.no_button = Gtk.Button.new_from_stock(Gtk.STOCK_NO)
        self.yes_button = Gtk.Button.new_from_stock(Gtk.STOCK_YES)
        self.pack_start(q_label, expand=True, fill=True, padding=0)
        self.pack_start(no_button, expand=False, padding=0)
        self.pack_start(yes_button, expand=False, padding=0)
        self.show_all()
    def set_button_sensitivity(self, no_sensitive, yes_sensitive):
        self.no_button.set_sensitive(no_sensitive)
        self.yes_button.set_sensitive(yes_sensitive)

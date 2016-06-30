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
from gi.repository import Gdk

from . import enotify
from . import icons
from . import gutils

APP_NAME = "epygibus"

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

class BusyIndicator(object):
    def __init__(self, parent=None):
        self.parent_indicator = parent
        self._count = 0
    def show_busy(self):
        if self.parent:
            self.parent.show_busy()
        self._count += 1
        if self._count == 1 and self.window:
            self.window.set_cursor(Gdk.Cursor(Gdk.WATCH))
            while Gtk.events_pending():
                Gtk.main_iteration()
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

class Dialog(Gtk.Dialog, BusyIndicator):
    def __init__(self, title=None, parent=None, flags=0, buttons=None):
        if not parent:
            parent = main_window
        Gtk.Dialog.__init__(self, title=title, parent=parent, flags=flags, buttons=buttons)
        if not parent:
            self.set_icon_from_file(icons.APP_ICON_FILE)
        BusyIndicator.__init__(self)
    def report_any_problems(self, result):
        report_any_problems(result, self)
    def inform_user(self, msg):
        inform_user(msg, parent=self)
    def warn_user(self, msg):
        warn_user(msg, parent=self)
    def alert_user(self, msg):
        alert_user(msg, parent=self)

class AmodalDialog(Dialog, enotify.Listener):
    def __init__(self, title=None, parent=None, flags=0, buttons=None):
        flags &= ~Gtk.DialogFlags.MODAL
        Dialog.__init__(self, title=title, parent=parent, flags=flags, buttons=buttons)
        enotify.Listener.__init__(self)
        self.set_type_hint(Gdk.WINDOW_TYPE_HINT_NORMAL)
        from . import ifce
    def _change_wd_cb(self, **kwargs):
        self.destroy()

class MessageDialog(Dialog):
    icons = {
        Gtk.MessageType.INFO: Gtk.STOCK_DIALOG_INFO,
        Gtk.MessageType.WARNING: Gtk.STOCK_DIALOG_WARNING,
        Gtk.MessageType.QUESTION: Gtk.STOCK_DIALOG_QUESTION,
        Gtk.MessageType.ERROR: Gtk.STOCK_DIALOG_ERROR,
    }
    labels = {
        Gtk.MessageType.INFO: _("FYI"),
        Gtk.MessageType.WARNING: _("Warning"),
        Gtk.MessageType.QUESTION: _("Question"),
        Gtk.MessageType.ERROR: _("Error"),
    }
    def __init__(self, parent=None, flags=Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT, type=Gtk.MessageType.INFO, buttons=None, message=None, explanation=None):
        if not parent:
            parent = main_window
        Dialog.__init__(self, title=APP_NAME + ": {0}".format(self.labels[type]), parent=parent, flags=flags, buttons=buttons)
        self.set_property("skip-taskbar-hint", True)
        hbox = Gtk.HBox()
        icon = Gtk.Image()
        icon.set_from_stock(self.icons[type], Gtk.IconSize.DIALOG)
        hbox.pack_start(icon, expand=False, fill=False, padding=0)
        label = Gtk.Label()
        label.set_markup("<big><b>" + self.labels[type] + "</b></big>")
        hbox.pack_start(label, expand=False, fill=False, padding=0)
        self.get_content_area().pack_start(hbox, expand=False, fill=False, padding=0)
        m_label = Gtk.Label()
        m_label.set_markup("<b>" + message + "</b>")
        self.get_content_area().pack_start(m_label, expand=True, fill=True, padding=0)
        if explanation:
            e_label = Gtk.Label(explanation)
            e_label.set_justify(Gtk.Justification.LEFT)
            self.get_content_area().pack_start(e_label, expand=True, fill=True, padding=0)
        self.show_all()
        self.set_resizable(True)

class QuestionDialog(Dialog):
    def __init__(self, title=None, parent=None, flags=0, buttons=None, question="", explanation=""):
        if title is None:
            title = APP_NAME
        Dialog.__init__(self, title=title, parent=parent, flags=flags, buttons=buttons)
        self.set_property("skip-taskbar-hint", True)
        hbox = Gtk.HBox()
        self.vbox.add(hbox)
        hbox.show()
        self.image = Gtk.Image()
        self.image.set_from_stock(Gtk.STOCK_DIALOG_QUESTION, Gtk.IconSize.DIALOG)
        hbox.pack_start(self.image, expand=False, fill=True, padding=0)
        self.image.show()
        q_label = Gtk.Label()
        q_label.set_markup("<big><b>" + question + "</b></big>")
        if explanation:
            vbox = Gtk.VBox()
            e_label = Gtk.Label(explanation)
            e_label.set_justify(Gtk.Justification.LEFT)
            vbox.pack_start(q_label, expand=True, fill=True, padding=0)
            vbox.pack_start(e_label, expand=True, fill=True, padding=0)
            hbox.add(vbox)
        else:
            hbox.add(q_label)
        self.show_all()

def ask_question(question, explanation="", parent=None,
                 buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK)):
    dialog = QuestionDialog(parent=parent,
                            flags=Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            buttons=buttons, question=question, explanation=explanation)
    response = dialog.run()
    dialog.destroy()
    return response

def ask_ok_cancel(question, explanation="", parent=None):
    return ask_question(question, explanation, parent) == Gtk.ResponseType.OK

def ask_yes_no(question, explanation="", parent=None):
    buttons = (Gtk.STOCK_NO, Gtk.ResponseType.NO, Gtk.STOCK_YES, Gtk.ResponseType.YES)
    return ask_question(question, explanation, parent, buttons) == Gtk.ResponseType.YES

def inform_user(msg, expln=None, parent=None, problem_type=Gtk.MessageType.INFO):
    dialog = MessageDialog(parent=parent,
                           flags=Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT,
                           type=problem_type, buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE),
                           message=msg, explanation=expln)
    dialog.run()
    dialog.destroy()

def warn_user(msg, expln=None, parent=None):
    inform_user(msg, expln, parent=parent, problem_type=Gtk.MessageType.WARNING)

def alert_user(msg, expln=None, parent=None):
    inform_user(msg, expln, parent=parent, problem_type=Gtk.MessageType.ERROR)

def report_any_problems(result, parent=None):
    if result.is_ok:
        return
    elif result.is_warning:
        problem_type = Gtk.MessageType.WARNING
    else:
        problem_type = Gtk.MessageType.ERROR
    inform_user("\n".join(result[1:]), parent, problem_type)

def report_failure(failure, parent=None):
    inform_user(failure.result, parent, Gtk.MessageType.ERROR)

def report_exception_as_error(edata, parent=None):
    problem_type = Gtk.MessageType.ERROR
    inform_user(str(edata), parent, problem_type)

class CancelOKDialog(Dialog):
    def __init__(self, title=None, parent=None):
        flags = Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        Dialog.__init__(self, title, parent, flags, buttons)

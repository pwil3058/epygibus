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
        self.gdk_window = self.get_window()
    def show_busy(self):
        if self.parent_indicator:
            self.parent_indicator.show_busy()
        self._count += 1
        if self._count == 1 and self.gdk_window:
            self.gdk_window.set_cursor(Gdk.Cursor(Gdk.WATCH))
            while Gtk.events_pending():
                Gtk.main_iteration()
    def unshow_busy(self):
        if self.parent_indicator:
            self.parent_indicator.unshow_busy()
        self._count -= 1
        assert self._count >= 0
        if self._count == 0 and self.gdk_window:
            self.gdk_window.set_cursor(None)
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
    alert_user(str(edata), parent=parent)

class CancelOKDialog(Dialog):
    def __init__(self, title=None, parent=None):
        if not parent:
            parent = main_window
        flags = Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT
        buttons = (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        Dialog.__init__(self, title, parent, flags, buttons)

class ReadTextWidget(Gtk.HBox):
    def __init__(self, prompt=None, suggestion="", width_chars=32):
        Gtk.HBox.__init__(self)
        if prompt:
            p_label = Gtk.Label()
            p_label.set_markup(prompt)
            self.pack_start(p_label, expand=False, fill=True, padding=0)
        self.entry = Gtk.Entry()
        if suggestion:
            self.entry.set_text(suggestion)
            self.entry.set_width_chars(max(width_chars, len(suggestion)))
        else:
            self.entry.set_width_chars(width_chars)
        self.pack_start(self.entry, expand=False, fill=True, padding=0)
        self.show_all()

class FileChooserDialog(Gtk.FileChooserDialog):
    def __init__(self, title=None, parent=None, action=Gtk.FileChooserAction.OPEN, buttons=None, backend=None):
        if not parent:
            parent = main_window
        Gtk.FileChooserDialog.__init__(self, title, parent, action, buttons, backend)

def select_directory(prompt, suggestion=None, existing=True, parent=None):
    if existing:
        if suggestion and not os.path.exists(suggestion):
            suggestion = None
    dialog = FileChooserDialog(prompt, parent, Gtk.FileChooserAction.SELECT_FOLDER,
                               (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                Gtk.STOCK_OK, Gtk.ResponseType.OK))
    dialog.set_default_response(Gtk.ResponseType.OK)
    if suggestion:
        if os.path.isdir(suggestion):
            dialog.set_current_folder(suggestion)
        else:
            dirname = os.path.dirname(suggestion)
            if dirname:
                dialog.set_current_folder(dirname)
    else:
        dialog.set_current_folder(os.getcwd())
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        new_dir_name = os.path.relpath(dialog.get_filename())
    else:
        new_dir_name = None
    dialog.destroy()
    return new_dir_name

class EnterDirPathWidget(Gtk.HBox):
    def __init__(self, prompt=None, suggestion=None, existing=True, width_chars=32, parent=None):
        Gtk.HBox.__init__(self)
        self._parent = parent
        self._dir_path = ReadTextWidget(prompt=prompt, suggestion=suggestion, width_chars=width_chars)
        self._existing = existing
        b_button = Gtk.Button.new_with_label(_("Browse"))
        b_button.connect("clicked", self._browse_cb)
        self.pack_start(self._dir_path, expand=True, fill=True, padding=0)
        self.pack_end(b_button, expand=False, fill=True, padding=0)
        self.show_all()
    @property
    def dir_path(self):
        return self._dir_path.entry.get_text()
    def _browse_cb(self, button=None):
        suggestion = self._dir_path.entry.get_text()
        dir_path = select_directory(_("Browse for Directory"), suggestion=suggestion, existing=self._existing, parent=self._parent)
        if dir_path:
            self._dir_path.entry.set_text(os.path.abspath(os.path.expanduser(dir_path)))

class EnterDirPathDialog(CancelOKDialog):
    def __init__(self, title=None, prompt=None, suggestion="", existing=True, parent=None):
        CancelOKDialog.__init__(self, title, parent)
        self.entry = EnterDirPathWidget(prompt, suggestion, existing, parent=self)
        self.get_content_area().add(self.entry)
        self.show_all()
    @property
    def dir_path(self):
        return self.entry.dir_path

def ask_dir_path(prompt, suggestion=None, existing=True, parent=None):
    dialog = EnterDirPathDialog(title=_("Enter Directory Path"), prompt=prompt, suggestion=suggestion, existing=existing, parent=parent)
    dir_path = dialog.dir_path if dialog.run() == Gtk.ResponseType.OK else None
    dialog.destroy()
    return dir_path

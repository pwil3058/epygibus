#!/usr/bin/python
### Copyright (C) 2013 Peter Williams <pwil3058@gmail.com>
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

'''GUI interface for managing a workspace using git and darning'''

import os
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

_BUG_TRACK_URL = 'https://github.com/pwil3058/epygibus/issues'
_DISCUSSION_EMAIL = 'pwil3058@gmail.com'
_REPORT_REQUEST_MSG = \
_('''<b>Please report this problem by either:
  submitting a bug report at &lt;{url}&gt;
or:
  e-mailing &lt;{email_address}&gt;
and including a copy of the details below this message.

Thank you.</b>
''').format(url=_BUG_TRACK_URL, email_address=_DISCUSSION_EMAIL)

def report_exception(exc_data, parent=None):
    def copy_cb(tview):
        tview.get_buffer().copy_clipboard(Gtk.clipboard_get())
    import traceback
    msg = ''.join(traceback.format_exception(exc_data[0], exc_data[1], exc_data[2]))
    dialog = Gtk.Dialog(title=_('gwsmgitd: Unhandled Exception'),
                        parent=parent, flags=Gtk.DialogFlags.MODAL|Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
    icon = Gtk.Image()
    icon.set_from_stock(Gtk.STOCK_DIALOG_ERROR, Gtk.IconSize.DIALOG)
    vbox = Gtk.VBox()
    vbox.pack_start(icon, expand=False, fill=False, padding=0)
    hbox = Gtk.HBox()
    hbox.pack_start(vbox, expand=False, fill=False, padding=0)
    label = Gtk.Label()
    label.set_selectable(True)
    label.set_markup(_REPORT_REQUEST_MSG)
    hbox.pack_start(label, expand=False, fill=False, padding=0)
    dialog.get_content_area().pack_start(hbox, expand=False, fill=False, padding=0)
    sbw = Gtk.ScrolledWindow()
    tview = Gtk.TextView()
    tview.set_editable(False)
    tview.get_buffer().set_text(msg)
    tview.connect('copy-clipboard', copy_cb)
    sbw.add(tview)
    dialog.get_content_area().pack_end(sbw, expand=True, fill=True, padding=0)
    dialog.show_all()
    dialog.set_resizable(True)
    dialog.run()
    dialog.destroy()

from . import cmd

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "gui",
    description=_("Launch the graphic user interface (GUI)."),
)

def run_cmd(args):
    try:
        from ..gui import main_window
    except Exception:
        report_exception(sys.exc_info())
        sys.exit(3)

    try:
        main_window.MainWindow().show()
        Gtk.main()
    except (SystemExit, KeyboardInterrupt):
        pass
    except Exception:
        report_exception(sys.exc_info())
        sys.exit(3)
    finally:
        pass

PARSER.set_defaults(run_cmd=run_cmd)

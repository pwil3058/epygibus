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

import os
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GdkPixbuf

from .. import APP_NAME

# find the icons directory
# first look in the source directory (so that we can run uninstalled)
_libdir = os.path.join(sys.path[0], "pixmaps")
if not os.path.exists(_libdir) or not os.path.isdir(_libdir):
    _TAILEND = os.path.join("share", "pixmaps", APP_NAME)
    _prefix = sys.path[0]
    while _prefix:
        _libdir = os.path.join(_prefix, _TAILEND)
        if os.path.exists(_libdir) and os.path.isdir(_libdir):
            break
        _prefix = os.path.dirname(_prefix)

APP_ICON = APP_NAME
APP_ICON_FILE = os.path.join(os.path.dirname(_libdir), APP_ICON + os.extsep + "png")
APP_ICON_PIXBUF = GdkPixbuf.Pixbuf.new_from_file(APP_ICON_FILE)

STOCK_REPO_SHOW = None
STOCK_NEW_REPO = Gtk.STOCK_NEW
STOCK_NEW_ARCHIVE = Gtk.STOCK_NEW
STOCK_REPO_DELETE = Gtk.STOCK_DELETE
STOCK_REPO_PRUNE = Gtk.STOCK_CUT
STOCK_INSERT = None
STOCK_OPEN_SNAPSHOT_FILE = Gtk.STOCK_OPEN
STOCK_DIR = Gtk.STOCK_DIRECTORY
STOCK_DIR_LINK = Gtk.STOCK_DIRECTORY
STOCK_FILE = Gtk.STOCK_FILE
STOCK_FILE_LINK = Gtk.STOCK_FILE
STOCK_EDIT_INCLUDES = Gtk.STOCK_EDIT
STOCK_EDIT_EXCLUDE_DIRS = Gtk.STOCK_EDIT
STOCK_EDIT_EXCLUDE_FILES = Gtk.STOCK_EDIT
STOCK_EXTRACT = None
STOCK_RESTORE = None

_FACTORY = Gtk.IconFactory()
_FACTORY.add_default()
_FACTORY.add(APP_ICON, Gtk.IconSet(APP_ICON_PIXBUF))

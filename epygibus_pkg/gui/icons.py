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
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GObject

APP_NAME = "epygibus"

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

STOCK_REPO_SHOW = None

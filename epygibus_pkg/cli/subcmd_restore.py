### Copyright (C) 2015 Peter Williams <pwil3058@gmail.com>
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

import sys
import os

from . import cmd

from .. import config
from .. import snapshot
from .. import excpns

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "restore",
    description=_("""Restore the contents of the nominated archive
    most recent (or specified) snapshot (or the nominated file/directory
    in that snapshot)."""),
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the archive to be restored (or restored from).")))

cmd.add_cmd_argument(PARSER, cmd.BACK_ISSUE_ARG())

XGROUP = PARSER.add_mutually_exclusive_group(required=True)

XGROUP.add_argument(
    "--file",
    help = _("the path of the file to be restored."),
    dest = "file_path",
    metavar = _("path"),
)

XGROUP.add_argument(
    "--dir",
    help = _("the path of the directory to be restored."),
    dest = "dir_path",
    metavar = _("path"),
)

XGROUP.add_argument(
    "--all",
    help = _("restore the complete snapshot."),
    action = "store_true",
)

def run_cmd(args):
    try:
        if args.file_path:
            snapshot.restore_file(args.archive_name, args.file_path, seln_fn=lambda l: l[-1-args.back])
        elif args.dir_path:
            snapshot.restore_subdir(args.archive_name, args.dir_path, seln_fn=lambda l: l[-1-args.back])
        elif args.all:
            snapshot.restore_subdir(args.archive_name, os.sep, seln_fn=lambda l: l[-1-args.back])
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    except EnvironmentError as edata:
        sys.stderr.write(_("Error: {}: {}\n").format(edata.strerror, edata.filename))
        sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

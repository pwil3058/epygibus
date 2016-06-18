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

import os
import errno
import sys

from . import cmd

from .. import config
from .. import snapshot
from .. import excpns

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "edit",
    description=_("Edit settings for nominated archive."),
)

XGROUP = PARSER.add_mutually_exclusive_group(required=True)

XGROUP.add_argument(
    "--includes", "-I",
    help=_("Edit the paths of file or directories to be included in the archive's snapshots."),
    action="store_true",
)

XGROUP.add_argument(
    "--excluded_dirs", "-Xd",
    help=_("Edit the glob expressions for directories to be excluded from this archive's snapshots."),
    action="store_true",
)

XGROUP.add_argument(
    "--excluded_files", "-Xf",
    help=_("Edit the glob expressions for files to be excluded from this archive's snapshots."),
    action="store_true",
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the archive to be edited.")))

def run_cmd(args):
    try:
        archive_spec = config.read_archive_spec(args.archive_name)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    try:
        if args.includes:
            file_path = config.get_includes_file_path(args.archive_name)
        elif args.excluded_dirs:
            file_path = config.get_exclude_dirs_file_path(args.archive_name)
        elif args.excluded_files:
            file_path = config.get_exclude_files_file_path(args.archive_name)
        editor = os.environ.get("EDITOR", "vi")
        os.execlp(editor, editor, file_path)
    except EnvironmentError as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

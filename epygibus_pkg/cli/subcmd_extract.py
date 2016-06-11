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

import sys
import os

from . import cmd

from .. import config
from .. import snapshot
from .. import excpns

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "extract",
    description=_("""Extract a copy of the nominated file/directory in the
    nominated archive's most recent (or specified) snapshot
    and place it in the current (or specified) directory."""),
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the archive to extract the copy of the file/directory from.")))

cmd.add_cmd_argument(PARSER, cmd.BACK_ISSUE_ARG())

XGROUP = PARSER.add_mutually_exclusive_group(required=True)

XGROUP.add_argument(
    "--file",
    help = _("the path of the file to be copied."),
    dest = "file_path",
    metavar = _("path"),
)

XGROUP.add_argument(
    "--dir",
    help = _("the path of the directory to be copied."),
    dest = "dir_path",
    metavar = _("path"),
)

PARSER.add_argument(
    "--into_dir",
    help = _("the path of the directory into which the file/directory is to be copied."),
    dest = "into_dir_path",
    default = os.curdir,
    metavar = _("path"),
)

PARSER.add_argument(
    "--with_name",
    help = _("the name to be given to the copy of the file/directory."),
    dest = "as_name",
    metavar = _("name"),
)

PARSER.add_argument(
    "--overwrite",
    help = _("overwrite the file/directory if it already exists."),
    action = "store_true",
)

def run_cmd(args):
    try:
        if args.file_path:
            snapshot.copy_file_to(args.archive_name, args.file_path, args.into_dir_path, seln_fn=lambda l: l[-1-args.back], as_name=args.as_name, overwrite=args.overwrite)
        else:
            snapshot.copy_subdir_to(args.archive_name, args.dir_path, args.into_dir_path, seln_fn=lambda l: l[-1-args.back], as_name=args.as_name, overwrite=args.overwrite)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    except EnvironmentError as edata:
        sys.stderr.write(_("Error: {}: {}\n").format(edata.strerror, edata.filename))
        sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

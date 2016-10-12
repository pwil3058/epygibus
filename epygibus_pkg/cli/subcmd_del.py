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
    "del",
    description=_("Delete the nominated archive's oldest (or specified) snapshot."),
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the arch(ive whose snapshot is to be deleted.")))

XPARSER = PARSER.add_mutually_exclusive_group(required=False)
cmd.add_cmd_argument(XPARSER, cmd.BACK_ISSUE_ARG(-1))

XPARSER.add_argument(
    "--all_but_newest",
    help=_("delete all but the N newest snapshots."),
    dest="newest_count",
    metavar=_("N"),
    type=int,
)

PARSER.add_argument(
    "--remove_last_ok",
    help=_("aurhorise deletion of the last snapshot in the archive."),
    action="store_true",
)

def run_cmd(args):
    if args.newest_count is not None:
        try:
            snapshot.delete_all_snapshots_but_newest(args.archive_name, newest_count=args.newest_count, clear_fell= args.remove_last_ok)
        except excpns.Error as edata:
            sys.stderr.write(str(edata) + "\n")
            sys.exit(-1)
    else:
        try:
            snapshot.delete_snapshot(args.archive_name, seln_fn=lambda l: l[-1-args.back], clear_fell= args.remove_last_ok)
        except excpns.Error as edata:
            sys.stderr.write(str(edata) + "\n")
            sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

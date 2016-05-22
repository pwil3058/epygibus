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

from . import cmd

from .. import config
from .. import snapshot
from .. import blobs
from .. import excpns

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "la",
    description=_("List the available snapshots in the nominated archive."),
    epilog=_("Snapshots will be listed in newest to oldest order unless specified otherwise."),
)

PARSER.add_argument(
    "--oldest_first",
    help=_("list snapshots in oldest to newest order."),
    action="store_false"
)

PARSER.add_argument("archive_name")

def run_cmd(args):
    try:
        snapshot_names = snapshot.get_snapshot_list(args.archive_name, reverse=args.oldest_first)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    for snapshot_name in snapshot_names:
        sys.stdout.write(snapshot_name + "\n")
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

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

import os
import sys

from . import cmd

from .. import config
from .. import blobs

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "list_blobs",
    description=_("List the blobs and reference counts for named repository."),
)

PARSER.add_argument(
    "repo_name",
    help=_("the name to be allocated to the content repository."),
    metavar=_("name"),
    action = "store"
)

def run_cmd(args):
    blob_mgr = blobs.open_repo(args.repo_name)
    for data in blob_mgr.iterate_hex_digests():
        sys.stdout.write(_("{}: {}\n").format(*data))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

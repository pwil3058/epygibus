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
    "cat",
    description=_("Print the contents of the nominated file in the nominated profile's most recent snapshot."),
)

PARSER.add_argument(
    "--profile",
    help=_("the name of the profile to extract the file content from."),
    required=True,
    dest="profile_name",
    metavar=_("name"),
)

PARSER.add_argument("file_path")

def run_cmd(args):
    try:
        snapshot_fs = snapshot.SnapshotFS(args.profile_name)
    except excpns.Error as edata:
        sys.stderr.write(str(edata))
        sys.exit(-1)
    try:
        snapshot_fs.cat_file(args.file_path, sys.stdout)
    except excpns.Error as edata:
        sys.stderr.write(str(edata))
        sys.exit(-2)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

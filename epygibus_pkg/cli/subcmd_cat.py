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

from . import cmd

from .. import config
from .. import snapshot
from .. import excpns

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "cat",
    description=_("Print the contents of the nominated file in the nominated archive's most recent (or specified) snapshot."),
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the archive to extract the file content from.")))

cmd.add_cmd_argument(PARSER, cmd.BACK_ISSUE_ARG())

PARSER.add_argument("file_path")

def run_cmd(args):
    try:
        snapshot_fs = snapshot.get_snapshot_fs(args.archive_name, seln_fn=lambda l: l[-1-args.back])
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    try:
        file_data = snapshot_fs.get_file(args.file_path)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-2)
    contents = file_data.open_read_only(binary=False).read()
    for line in contents.splitlines(True):
        sys.stdout.write(line)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

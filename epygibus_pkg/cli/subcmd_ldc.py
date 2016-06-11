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
    "ldc",
    description=_("List list the contents of the named directory in the nominated archive's most recent (or specified) snapshot."),
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the archive whose files are to be listed.")))

cmd.add_cmd_argument(PARSER, cmd.BACK_ISSUE_ARG())

PARSER.add_argument("in_dir_path")

def run_cmd(args):
    try:
        snapshot_fs = snapshot.get_snapshot_fs(args.archive_name, seln_fn=lambda l: l[-1-args.back]).get_subdir(args.in_dir_path)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    try:
        for dir_data in sorted(snapshot_fs.iterate_subdirs()):
            sys.stdout.write(dir_data.path + os.sep + "\n")
        for dir_link_data in sorted(snapshot_fs.iterate_subdir_links()):
            sys.stdout.write(dir_link_data.path + os.sep + " -> " + dir_link_data.tgt_path + os.sep + "\n")
        for file_data in sorted(snapshot_fs.iterate_files()):
            sys.stdout.write(file_data.path + "\n")
        for file_link_data in sorted(snapshot_fs.iterate_file_links()):
            sys.stdout.write(file_link_data.path + " -> " + file_link_data.tgt_path + "\n")
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

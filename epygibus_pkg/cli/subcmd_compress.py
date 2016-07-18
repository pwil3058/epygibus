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
from .. import repo
from .. import excpns
from .. import utils

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "compress",
    description=_("Compress/uncompress the nominated archive's latest (or specified) snapshot."),
)

MXGROUP = PARSER.add_mutually_exclusive_group()
cmd.add_cmd_argument(MXGROUP, cmd.REPO_NAME_ARG(_("the name of the repository whose content items are to be compressed/uncompressed."), False))
cmd.add_cmd_argument(MXGROUP, cmd.ARCHIVE_NAME_ARG(_("the name of the archive whose snapshot is to be compressed/uncompressed."), False))
cmd.add_cmd_argument(PARSER, cmd.BACK_ISSUE_ARG())

PARSER.add_argument(
    "--uncompress", "-U",
    help=_("do uncompression instead of (the default) compression."),
    action="store_true"
)

def run_cmd(args):
    try:
        if args.archive_name:
            if args.uncompress:
                try:
                    snapshot.uncompress_snapshot(args.archive_name, seln_fn=lambda l: l[-1-args.back])
                except excpns.SnapshotNotCompressed:
                    sys.stdout.write(_("Nothing to do.\n"))
            else:
                try:
                    snapshot.compress_snapshot(args.archive_name, seln_fn=lambda l: l[-1-args.back])
                except excpns.SnapshotAlreadyCompressed:
                    sys.stdout.write(_("Nothing to do.\n"))
        else:
            if args.uncompress:
                size_change = repo.uncompress_repository(args.repo_name)
                sys.stdout.write(_("Disk usage increased by {}.\n").format(utils.format_bytes(size_change)))
            else:
                size_change = repo.compress_repository(args.repo_name)
                sys.stdout.write(_("Disk usage decreased by {}.\n").format(utils.format_bytes(size_change)))
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

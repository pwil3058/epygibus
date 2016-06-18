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
    "new",
    description=_("Create a new snapshot archive."),
    epilog=_("By default broken soft links are skipped unless otherwise specified."),
)

PARSER.add_argument(
    "--location",
    help=_("The directory path of the location in which the archive is to be created."),
    dest="location_dir_path",
    required=True,
    metavar=_("directory"),
)

cmd.add_cmd_argument(PARSER, cmd.REPO_NAME_ARG(_("The name of the content repository to be used with this archive.")))

PARSER.add_argument(
    "--include", "-I",
    help=_("The path of a file or directory to be included in this archive's snapshots."),
    dest="includes",
    action="append",
    required=True,
    metavar=_("path"),
)

PARSER.add_argument(
    "--exclude_dirs_matching", "-Xd",
    help=_("Exclude directories matching this glob expression from this archive's snapshots."),
    dest="exclude_dir_globs",
    action="append",
    metavar=_("regexp"),
)

PARSER.add_argument(
    "--exclude_files_matching", "-Xf",
    help=_("Exclude files matching this glob expression from this archive's snapshots."),
    dest="exclude_file_globs",
    action="append",
    metavar=_("regexp"),
)

PARSER.add_argument(
    "--keep_broken_soft_links",
    help=_("Keep broken soft links."),
    dest="skip_broken_sl",
    action="store_false"
)


cmd.add_cmd_argument(PARSER, cmd.UNCOMPRESSED_ARG(_("set default snapshot compression option to \"compress\" insteatd of\"uncompress\".")))

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name to be allocated to this snapshot archive.")))

def run_cmd(args):
    try:
        repo_spec = config.read_repo_spec(args.repo_name)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    try:
        snapshot.create_new_archive(
            archive_name=args.archive_name,
            location_dir_path=args.location_dir_path,
            repo_spec=repo_spec,
            includes=args.includes,
            exclude_dir_globs=args.exclude_dir_globs,
            exclude_file_globs=args.exclude_file_globs,
            skip_broken_sl=args.skip_broken_sl,
            compress_default=not args.uncompressed
        )
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

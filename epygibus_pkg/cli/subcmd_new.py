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
import errno
import sys

from . import cmd

from .. import config
from .. import blobs

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "new",
    description=_("Create a new snapshot archive."),
    epilog=_("By default broken soft links are skipped unless otherwise specified."),
)

PARSER.add_argument(
    "--location",
    help=_("The directory path of the location in which the archive is to be created."),
    dest="location_dir_path",
    default=".",
    metavar=_("directory"),
)

PARSER.add_argument(
    "--repo", "-R",
    help=_("The name of the content repository to be used with this archive."),
    dest="repo_name",
    required=True,
    metavar=_("name"),
)

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
    help=_("Exclude directories matching this regular expression this archive's snapshots."),
    dest="exclude_dir_res",
    action="append",
    metavar=_("regexp"),
)

PARSER.add_argument(
    "--exclude_files_matching", "-Xf",
    help=_("Exclude files matching this regular expression this archive's snapshots."),
    dest="exclude_file_res",
    action="append",
    metavar=_("regexp"),
)

PARSER.add_argument(
    "--keep_broken_soft_links",
    help=_("Keep broken soft links."),
    dest="skip_broken_sl",
    action="store_false"
)

PARSER.add_argument(
    "archive_name",
    help=_("the name to be allocated to the snapshot archive."),
    metavar=_("name"),
    action = "store"
)

def run_cmd(args):
    try:
        config.read_repo_spec(args.repo_name)
    except IOError as edata:
        if edata.errno == errno.ENOENT:
            sys.stderr.write(_("Error: unknown content repository: {}\n").format(args.repo_name))
            sys.exit(-1)
        else:
            raise edata
    try:
        base_dir_path = config.write_archive_spec(
            archive_name=args.archive_name,
            in_dir_path=args.location_dir_path,
            repo_name=args.repo_name,
            includes=args.includes,
            exclude_dirs=args.exclude_dir_res if args.exclude_dir_res else [],
            exclude_files=args.exclude_file_res if args.exclude_file_res else [],
            skip_broken_sl=args.skip_broken_sl
        )
    except OSError as edata:
        if edata.errno == errno.EEXIST:
            sys.stderr.write(_("Error: snapshot archive \"{}\" already defined.\n").format(args.archive_name))
            sys.exit(-1)
        else:
            raise edata
    try:
        os.makedirs(base_dir_path)
    except OSError as edata:
        if edata.errno == errno.EEXIST:
            sys.stderr.write(_("Error: location for snapshot archive \"{}\" already exists.\n").format(args.archive_name))
            sys.exit(-1)
        elif edata.errno == errno.EPERM:
            sys.stderr.write(_("Error: permission denied creating location for snapshot archive \"{}\".\n").format(args.archive_name))
            sys.exit(-1)
        else:
            raise edata
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

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
from .. import excpns
from .. import utils

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "show",
    description=_("Show description of the nominated archive."),
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the archive to be described.")))

def run_cmd(args):
    try:
        archive = config.read_archive_spec(args.archive_name)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    sys.stdout.write(_("Archive: {}\n").format(archive.name))
    sys.stdout.write(_("  Repository: {}\n").format(archive.repo_name))
    sys.stdout.write(_("  Snapshot Dir: {}\n").format(archive.snapshot_dir_path))
    sys.stdout.write(_("  Skip Broken Soft Links: {}\n").format(archive.skip_broken_soft_links))
    sys.stdout.write(_("  Compress Snapshots By Default: {}\n").format(archive.compress_default))
    sys.stdout.write(_("Includes:\n"))
    for i in archive.includes:
        sys.stdout.write("  {}\n".format(i))
    if archive.exclude_dir_globs:
        sys.stdout.write(_("Excludes directories matching:\n"))
        for e in archive.exclude_dir_globs:
            sys.stdout.write("  {}\n".format(e))
    if archive.exclude_file_globs:
        sys.stdout.write(_("Excludes files matching:\n"))
        for e in archive.exclude_file_globs:
            sys.stdout.write("  {}\n".format(e))
    try:
        first = True
        for name, size, statistics in snapshot.iter_snapshot_list(archive.name, reverse=False):
            if first:
                first = False
                sys.stdout.write(_("Snapshots:                 Occupies    #Files    #Links        Holds New Blobs   CPU Time Total Time    IO Time\n"))
            nfiles, nlinks, csize, new_blobs, etd = statistics
            sys.stdout.write("  {}: {:>12} {:>9,} {:>9,} {:>12} {:>9,} {:>10.2f} {:>10.2f} {:>10.2f}\n".format(name, utils.format_bytes(size), nfiles, nlinks, utils.format_bytes(csize), new_blobs, *etd))
        if first:
            sys.stdout.write(_("Snapshots: None\n"))
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

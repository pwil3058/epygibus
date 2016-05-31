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

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "bu",
    description=_("Take a back up snapshot for the nominated archives."),
)

PARSER.add_argument(
    "archives",
    help=_("the name(s) of the archive(s) for which the back up snapshot(s) is/are to be taken."),
    nargs="+",
    metavar=_("archive"),
)

PARSER.add_argument(
    "--stats",
    help=_("print the statistics for reach archive."),
    action="store_true"
)

PARSER.add_argument(
    "--paranoid",
    help=_("don't use data (size, m_time) from previous snapshot to speed up content processing."),
    action="store_true"
)

def run_cmd(args):
    # read all archives in one go so that if any fails checks we do nothing
    try:
        archives = [(archive_name, config.read_archive_spec(archive_name)) for archive_name in args.archives]
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    for archive_name, archive in archives:
        stats = snapshot.generate_snapshot(archive, use_previous=not args.paranoid, stderr=sys.stderr)
        if args.stats:
            sys.stdout.write(_("{0} STATS: {1}\n").format(archive_name, stats))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

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
    "lss",
    description=_("List the available snapshots in the nominated archive."),
    epilog=_("Snapshots will be listed in oldest to newest order unless specified otherwise."),
)

PARSER.add_argument(
    "--newest_first",
    help=_("list snapshots in newest to oldest order."),
    action="store_true"
)

XGROUP = PARSER.add_mutually_exclusive_group()

XGROUP.add_argument(
    "--build_stats",
    help=_("show statistics gathered during build."),
    action="store_true"
)

XGROUP.add_argument(
    "--storage_stats",
    help=_("show storage statistics."),
    action="store_true"
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(_("the name of the archive whose snapshots are to be listed.")))

def run_cmd(args):
    if args.build_stats:
        try:
            first = True
            for name, size, statistics in snapshot.iter_snapshot_list(args.archive_name, args.newest_first):
                if first:
                    first = False
                    sys.stdout.write(_("Snapshots:                 Occupies    #Files    #Links        Holds New Citem Time(secs)    Breakdown(CPU/IO)\n"))
                nfiles, nlinks, csize, new_citems, _spare, etd = statistics
                sys.stdout.write("  {}: {:>12} {:>9,} {:>9,} {:>12} {:>9,} {:>10.2f}    ({:>6.2f}%/{:>6.2f}%)\n".format(name, utils.format_bytes(size), nfiles, nlinks, utils.format_bytes(csize), new_citems, etd.real_time, etd.percent_cpu, etd.percent_io))
        except excpns.Error as edata:
            sys.stderr.write(str(edata) + "\n")
            sys.exit(-1)
    elif args.storage_stats:
        try:
            first = True
            for snapshot_fs, size in snapshot.iter_snapshot_fs_list(args.archive_name, args.newest_first):
                if first:
                    first = False
                    sys.stdout.write(_("Snapshots:                 Occupies    #Files    #Links        Holds    #Items       Stored        Share\n"))
                nfiles, nlinks, csize, n_citems, stored_size, share = snapshot_fs.get_statistics()
                sys.stdout.write("  {}: {:>12} {:>9,} {:>9,} {:>12} {:>9,} {:>12} {:>12}\n".format(snapshot_fs.snapshot_name, utils.format_bytes(size), nfiles, nlinks, utils.format_bytes(csize), n_citems, utils.format_bytes(stored_size), utils.format_bytes(share)))
        except excpns.Error as edata:
            sys.stderr.write(str(edata) + "\n")
            sys.exit(-1)
    else:
        try:
            snapshot_data_list = snapshot.get_snapshot_name_list(args.archive_name, reverse=args.newest_first)
        except excpns.Error as edata:
            sys.stderr.write(str(edata) + "\n")
            sys.exit(-1)
        for snapshot_data in snapshot_data_list:
            if snapshot_data[1]:
                sys.stdout.write("{}**\n".format(snapshot_data[0]))
            else:
                sys.stdout.write("{}\n".format(snapshot_data[0]))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

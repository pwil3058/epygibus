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
    "bu",
    description=_("Take a back up snapshot for the nominated archives."),
    epilog=_("More than one --archive can be specified, if requited.")
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(help_msg=_("the name of the archive for which the back up snapshot is/are to be taken."), action="append"))

PARSER.add_argument(
    "--stats",
    help=_("print the statistics for each archive."),
    action="store_true"
)

PARSER.add_argument(
    "--quiet",
    help=_("don't report broken soft links skipped during processing."),
    action="store_true"
)

MXGROUP = PARSER.add_mutually_exclusive_group()
cmd.add_cmd_argument(MXGROUP, cmd.COMPRESSED_ARG(_("override the default and create a compressed snapshot file.")))
cmd.add_cmd_argument(MXGROUP, cmd.UNCOMPRESSED_ARG(_("override the default and create an uncompressed snapshot file.")))

def run_cmd(args):
    # read all archives in one go so that if any fails checks we do nothing
    compress = True if args.compressed else False if args.uncompressed else None
    try:
        archives = [(archive_name, config.read_archive_spec(archive_name)) for archive_name in args.archive_name]
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    if args.stats:
        ARCHIVE_HDR = _("Archive")
        len_longest_name = max(len(max(args.archive_name, key=len)), len(ARCHIVE_HDR))
        TEMPL = "{:>" + str(len_longest_name) + "}: {}: {}:"
        sys.stdout.write(" " * (len_longest_name - len(ARCHIVE_HDR) + 75) + "Content Items         Time Taken\n")
        sys.stdout.write(" " * (len_longest_name - len(ARCHIVE_HDR)) + ARCHIVE_HDR + ":")
        sys.stdout.write(_("            Snapshot:   Occupies:   #files    #links      Holding  #Created #Released    Build(%I/O)     Write\n"))
    for archive_name, archive in archives:
        stats = snapshot.generate_snapshot(archive, stderr=sys.stderr, report_skipped_links=not args.quiet, compress=compress)
        if args.stats:
            ss_name, ss_size, ss_stats, write_etd = stats
            sys.stdout.write(TEMPL.format(archive_name, ss_name, utils.format_bytes(ss_size)))
            nfiles, nlinks, csize, new_citems, rel_citems, construction_etd = ss_stats
            sys.stdout.write("{:>9,} {:>9,} {:>12} {:>9,} {:>9,}".format(nfiles, nlinks, utils.format_bytes(csize), new_citems, rel_citems))
            sys.stdout.write("{:>8.2f}s({:>4.1f}) {:>8.2f}s\n".format(construction_etd.real_time, construction_etd.percent_io, write_etd.real_time))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

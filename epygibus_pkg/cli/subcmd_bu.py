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
    epilog=_("More than one --archive can be specified, if requited.\n\nIn general, --trusting will only speed up the taking of a snapshot if the previous snapshot is not compressed due to the time taken to decompress the previous archive.")
)

cmd.add_cmd_argument(PARSER, cmd.ARCHIVE_NAME_ARG(help_msg=_("the name of the archive for which the back up snapshot is/are to be taken."), action="append"))

PARSER.add_argument(
    "--stats",
    help=_("print the statistics for reach archive."),
    action="store_true"
)

PARSER.add_argument(
    "--trusting",
    help=_("use data (size, m_time) from previous snapshot to (possibly) speed up content processing."),
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
    for archive_name, archive in archives:
        stats = snapshot.generate_snapshot(archive, use_previous=args.trusting, stderr=sys.stderr, report_skipped_links=not args.quiet, compress=compress)
        if args.stats:
            sys.stdout.write(_("{0} STATS: {1}\n").format(archive_name, stats))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

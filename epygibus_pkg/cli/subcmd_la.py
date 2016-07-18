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
from .. import excpns

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "la",
    description=_("List the names of the available snapshot archives."),
)

def run_cmd(args):
    try:
        archive_name_list = config.get_archive_name_list()
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    for archive_name in archive_name_list:
        sys.stdout.write("{}\n".format(archive_name))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

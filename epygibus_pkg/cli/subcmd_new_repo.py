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

import sys

from . import cmd

from .. import repo
from .. import excpns

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "new_repo",
    description=_("Create a new content repository."),
)

PARSER.add_argument(
    '--location',
    help=_("The directory path of the location in which the repository is to be created."),
    dest='location_dir_path',
    default=".",
    metavar=_('directory'),
)

PARSER.add_argument(
    "repo_name",
    help=_("the name to be allocated to the content repository."),
    metavar=_("name"),
    action = "store"
)

cmd.add_cmd_argument(PARSER, cmd.UNCOMPRESSED_ARG())

def run_cmd(args):
    try:
        repo.create_new_repo(args.repo_name, args.location_dir_path, compressed=not args.uncompressed)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

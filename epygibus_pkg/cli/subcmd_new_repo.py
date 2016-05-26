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

from . import cmd

from .. import config
from .. import blobs

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

def run_cmd(args):
    base_dir_path = config.write_repo_spec(args.repo_name, args.location_dir_path)
    os.makedirs(base_dir_path)
    blobs.initialize_repo(base_dir_path)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

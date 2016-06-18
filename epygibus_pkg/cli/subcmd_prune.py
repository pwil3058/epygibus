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
import sys

from . import cmd

from .. import config
from .. import repo
from .. import excpns
from .. import utils

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "prune",
    description=_("Remove unreferenced content items in the named repository."),
)

cmd.add_cmd_argument(PARSER, cmd.REPO_NAME_ARG())

def run_cmd(args):
    try:
        repo_mgmt_key = repo.get_repo_mgmt_key(args.repo_name)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    stats = None
    with repo.open_repo_mgr(repo_mgmt_key, writeable=True) as repo_mgr:
        stats = repo_mgr.prune_unreferenced_content()
    if not stats:
        sys.stdout.write(_("Nothing to do.\n"))
    else:
        sys.stdout.write(_("{:>4,} unreferenced content items removed freeing {}\n").format(stats[0], utils.format_bytes(stats[1])))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

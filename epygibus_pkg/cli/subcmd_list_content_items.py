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
    "list_content_items",
    description=_("List the content items and reference counts for named repository."),
)

cmd.add_cmd_argument(PARSER, cmd.REPO_NAME_ARG())

def run_cmd(args):
    try:
        repo_mgmt_key = repo.get_repo_mgmt_key(args.repo_name)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    total_citems = 0
    total_ref_count = 0
    total_content_size = 0
    total_stored_size = 0
    with repo.open_repo_mgr(repo_mgmt_key, writeable=False) as repo_mgr:
        for content_token, ref_count, content_size, stored_size in repo_mgr.iterate_content_tokens():
            total_citems += 1
            total_ref_count += ref_count
            total_content_size += content_size
            total_stored_size += stored_size
            sys.stdout.write(_("{}: {:>4,}: {} ({})\n").format(content_token, ref_count, utils.format_bytes(content_size), utils.format_bytes(stored_size)))
    sys.stdout.write(_("{:,} content items: {:>4,} references: {} ({}) total\n").format(total_citems, total_ref_count, utils.format_bytes(total_content_size), utils.format_bytes(total_stored_size)))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

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
import sys

from . import cmd

from .. import config
from .. import repo
from .. import excpns
from .. import utils

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "repo_stats",
    description=_("Show vital statistics for named repository."),
)

cmd.add_cmd_argument(PARSER, cmd.REPO_NAME_ARG())

def run_cmd(args):
    try:
        repo_mgmt_key = repo.get_repo_mgmt_key(args.repo_name)
    except excpns.Error as edata:
        sys.stderr.write(str(edata) + "\n")
        sys.exit(-1)
    total_referenced_citems = 0
    total_ref_count = 0
    total_referenced_size = 0
    total_unreferenced_citems = 0
    total_unreferenced_size = 0
    with repo.open_repo_mgr(repo_mgmt_key, writeable=False) as repo_mgr:
        for hex_digest, ref_count, size in repo_mgr.iterate_hex_digests():
            if ref_count:
                total_referenced_citems += 1
                total_ref_count += ref_count
                total_referenced_size += size
            else:
                total_unreferenced_citems += 1
                total_unreferenced_size += size
    sys.stdout.write(_("  Referenced {:,} content items: {:>4,} references: {} total\n").format(total_referenced_citems, total_ref_count, utils.format_bytes(total_referenced_size)))
    sys.stdout.write(_("Unreferenced {:,} content items: {:>4,} references: {} total\n").format(total_unreferenced_citems, 0, utils.format_bytes(total_unreferenced_size)))
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

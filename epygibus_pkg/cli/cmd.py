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

"""
Provide command line parsing mechanism including provision of a
mechanism for sub commands to add their components.
"""

import argparse
import collections

from .. import VERSION

_ARG_SPEC = collections.namedtuple("_ARG_SPEC", ["args", "kargs"])
def add_cmd_argument(parser, arg_spec):
    parser.add_argument(*arg_spec.args, **arg_spec.kargs)

PARSER = argparse.ArgumentParser(description=_("Manage file back ups"))

PARSER.add_argument(
    "--version",
    action="version",
    version=VERSION
)

REPO_NAME_ARG = lambda help_msg=_("The name of the repository."), required=True : _ARG_SPEC(
    ["--repo", "-R",],
    {
        "help": help_msg,
        "dest": "repo_name",
        "required": required,
        "metavar": _("name"),
    }
)

ARCHIVE_NAME_ARG = lambda help_msg=_("The name of the archive."), required=True, action="store" : _ARG_SPEC(
    ["--archive", "-A",],
    {
        "help": help_msg,
        "dest": "archive_name",
        "required": required,
        "action": action,
        "metavar": _("name"),
    }
)

snapshot_dir_explanation = _("""
The --exigency option is not intended for normal use.  It is
intended for the exigency where the repository and archive specification
files have been lost due a file system failure.
""")

SNAPSHOT_DIR_ARG = lambda help_msg=_("The path of the directory containing the archive's snapshot(s)."), required=True, action="store" : _ARG_SPEC(
    ["--exigency", "-E",],
    {
        "help": help_msg,
        "dest": "snapshot_dir_path",
        "required": required,
        "action": action,
        "metavar": _("snapshot_dir_path"),
    }
)

BACK_ISSUE_ARG = lambda default=0 : _ARG_SPEC(
    ["--back",],
    {   "help": _("select the snapshot \"N\" places before the most recent. Use -1 to select oldest. Defaults to {}.").format(default),
        "default": default,
        "type": int,
        "metavar": _("N"),
    }
)

COMPRESSED_ARG = lambda help_msg=_("store data compressed."): _ARG_SPEC(
    ["--compressed", "-C"],
    {   "help": help_msg,
        "action": "store_true",
    }
)

UNCOMPRESSED_ARG = lambda help_msg=_("store data uncompressed."): _ARG_SPEC(
    ["--uncompressed", "-U"],
    {   "help": help_msg,
        "action": "store_true",
    }
)

SUB_CMD_PARSER = PARSER.add_subparsers(title=_("commands"))

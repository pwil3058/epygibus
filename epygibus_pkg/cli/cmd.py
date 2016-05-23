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

BACK_ISSUE_ARG = _ARG_SPEC(
    ["--back",],
    {   "help": _("select the snapshot \"N\" places before the most recent."),
        "default": 0,
        "type": int,
        "metavar": _("N"),
    }
)


SUB_CMD_PARSER = PARSER.add_subparsers(title=_("commands"))

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

from . import cli_args

PARSER = cli_args.SUB_CMD_PARSER.add_parser(
    "bu",
    description=_("Take a back up snapshot for the nominated profiles."),
)

PARSER.add_argument(
    'profiles',
    help=_("the name(s) of the profile(s) for which the back up snapshots are to be taken."),
    nargs='+',
    metavar=_('profile'),
)

def run_cmd(args):
    for profile in args.profiles:
        print "Processing:", profile
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

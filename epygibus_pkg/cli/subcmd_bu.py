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

from . import cmd

from .. import config
from .. import snapshot

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "bu",
    description=_("Take a back up snapshot for the nominated profiles."),
)

PARSER.add_argument(
    "profiles",
    help=_("the name(s) of the profile(s) for which the back up snapshot(s) is/are to be taken."),
    nargs="+",
    metavar=_("profile"),
)

PARSER.add_argument(
    "--stats",
    help=_("print the statistics for reach profile."),
    action="store_true"
)

def run_cmd(args):
    # read all profiles in one go so that if any fails checks we do nothing
    profiles = [(profile_name, config.read_profile_spec(profile_name)) for profile_name in args.profiles]
    for profile_name, profile in profiles:
        if args.stats:
            print "{0} STATS:".format(profile_name), snapshot.generate_snapshot(profile)
        else:
            snapshot.generate_snapshot(profile)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

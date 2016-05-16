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
from .. import snapshot
from .. import blobs

PARSER = cmd.SUB_CMD_PARSER.add_parser(
    "cat",
    description=_("Print the contents of the nominated file in the nominated profile's most recent snapshot."),
)

PARSER.add_argument(
    "--profile",
    help=_("the name of the profile to extract the file content from."),
    required=True,
    dest="profile_name",
    metavar=_("name"),
)

PARSER.add_argument("file_path")

def run_cmd(args):
    try:
        profile = config.read_profile_spec(args.profile_name)
    except IOError as edata:
        sys.stderr.write("Unknown profile: {}.\n".format(args.profile_name))
        sys.exit(-1)
    latest_snapshot = snapshot.read_most_recent_snapshot(profile.snapshot_dir_path)
    try:
        file_data = latest_snapshot.get_file(args.file_path)
    except KeyError:
        sys.stderr.write("Unknown file: {}.\n".format(args.file_path))
        sys.exit(-2)
    repo = blobs.open_repo(profile.repo_name)
    contents = repo.fetch_contents(file_data.payload)
    for line in contents.splitlines(True):
        sys.stdout.write(line)
    return 0

PARSER.set_defaults(run_cmd=run_cmd)

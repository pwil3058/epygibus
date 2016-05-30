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

# This should be the only place that subcmd_* modules should be imported
# as this is sufficient to activate them.
from . import subcmd_bu
from . import subcmd_new_repo
from . import subcmd_cat
from . import subcmd_new
from . import subcmd_la
from . import subcmd_ldc
from . import subcmd_del
from . import subcmd_list_blobs
from . import subcmd_repo_stats
from . import subcmd_prune

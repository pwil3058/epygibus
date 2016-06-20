### Copyright (C) 2016 Peter Williams <pwil3058@gmail.com>
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
import collections

class ETD(collections.namedtuple("ETD", ["cpu_time", "real_time", "io_time"])):
    def __add__(self, other):
        return ETD(*(self[i] + other[i] for i in range(len(self))))
    def __sub__(self, other):
        return ETD(*(self[i] - other[i] for i in range(len(self))))
    @property
    def percent_io(self):
        try:
            return (100.0 * self.io_time) / self.real_time
        except ZeroDivisionError:
            return 100.0

class OsTimes(collections.namedtuple("OsTimes", ["utime", "stime", "cutime", "cstime", "rtime"])):
    def __sub__(self, other):
        return OsTimes(*(self[i] - other[i] for i in range(len(self))))
    def __add__(self, other):
        return OsTimes(*(self[i] + other[i] for i in range(len(self))))
    def get_etd(self):
        cpu_time = self.utime + self.stime
        return ETD(cpu_time, self.rtime, max(self.rtime - cpu_time, 0))

def get_os_times():
    return OsTimes(*os.times())

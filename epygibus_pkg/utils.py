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


def format_bytes(number, decimal_pts=3):
    fmt_str = "{{:>{},.{}f}} {{}}".format(4 + decimal_pts, decimal_pts)
    if number < 1000000:
        return fmt_str.format(float(number)/1000, "Kb")
    elif number < 1000000000:
        return fmt_str.format(float(number)/1000000, "Mb")
    elif number < 1000000000000:
        return fmt_str.format(float(number)/1000000000, "Gb")
    else:
        return fmt_str.format(float(number)/1000000000000, "Tb")
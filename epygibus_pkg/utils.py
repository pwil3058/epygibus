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

import os

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

def compress_file(file_path):
    assert not file_path.endswith(".gz")
    import gzip
    import shutil

    out_file_path = file_path + ".gz"
    with open(file_path, "rb") as f_in, gzip.open(out_file_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(file_path)
    return os.path.getsize(out_file_path)

def uncompress_file(file_path):
    assert file_path.endswith(".gz")
    import gzip
    import shutil

    out_file_path = file_path[0:-3]
    with gzip.open(file_path, "rb") as f_in, open(out_file_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(file_path)
    return os.path.getsize(out_file_path)

def is_rel_path(path):
    return not os.path.isabs(os.path.expanduser(path))

def calc_link_tgt_abs_path(link_tgt_path, link_file_path):
    e_path = os.path.expanduser(link_tgt_path)
    if os.path.isabs(e_path):
        return e_path
    return os.path.abspath(os.path.join(os.path.dirname(link_file_path), link_tgt_path))

def get_link_tgt_abs_path(link_file_path):
    return calc_link_tgt_abs_path(os.readlink(link_file_path), link_file_path)

def is_broken_link(link_tgt_path, link_file_path):
    return not os.path.exists(calc_link_tgt_abs_path(link_tgt_path, link_file_path))

class DummyProgressThingy:
    def set_expected_total(self, total):
        pass
    def increment_count(self, by=1):
        pass
    def finished(self):
        pass

class DummyActivityIndicator:
    def start(self, only_every=0):
        pass
    def pulse(self):
        pass
    def finished(self):
        pass

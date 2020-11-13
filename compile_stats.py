#!/usr/bin/python3

#    Collect stats from a processes maps file
#    Copyright (C) 2020  Eric B Munson
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse
import sys
import json
import statistics


def compute_stats(lst, num_procs=1):
    ret = dict()
    sizes_kb = [entry['size_kb'] for entry in lst]
    exe_count = 0
    shared_count = 0
    for entry in lst:
        if entry['is_shared']:
            shared_count += 1
        if entry['is_exe']:
            exe_count += 1
    ret['count'] = len(lst)
    ret['size_mean'] = statistics.mean(sizes_kb)
    ret['size_median'] = statistics.median(sizes_kb)
    ret['size_stddev'] = statistics.pstdev(sizes_kb, ret['size_mean'])
    ret['shared_count'] = shared_count
    ret['exe_count'] = exe_count
    ret['num_procs'] = num_procs
    if num_procs != 1:
        ret['count_mean'] = ret['count'] / num_procs
    return ret


def read_file(file_path):
    with open(file_path, 'r') as fd:
        stats = json.load(fd)
    num_procs = len(stats['counts'])
    anon = compute_stats(stats['anonymous'], num_procs)
    guard = compute_stats(stats['guard'], num_procs)
    code = compute_stats(stats['code'], num_procs)
    stack = compute_stats(stats['stack'], num_procs)
    kernel_shared = compute_stats(stats['kernel_shared'], num_procs)
    heap = compute_stats(stats['heap'], num_procs)
    data = compute_stats(stats['data'], num_procs)
    return anon, guard, code, stack, kernel_shared, heap, data


def main():
    parser = argparse.ArgumentParser(description="Read one or more JSON files and assemble VMA stats")
    parser.add_argument("files", type=str, help="One or more JSON files to parse",
                        nargs='+')
    args = parser.parse_args(sys.argv[1:])

    for entry in args.files:
        print("Stats for {}:".format(entry))
        a,g,c,s,k,h,d = read_file(entry)
        print("Anonymous: {}".format(a))
        print("Guard: {}".format(g))
        print("Code: {}".format(c))
        print("Stack: {}".format(s))
        print("VDSO or vvar: {}".format(k))
        print("Heap: {}".format(h))
        print("Data: {}".format(d))


if __name__ == "__main__":
    main()
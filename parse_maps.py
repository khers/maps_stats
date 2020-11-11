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


import psutil
import argparse
import sys
import json
import re

def maps_lines(file_path):
    with open(file_path, "r") as fd:
        for line in fd:
            line = re.sub(r'\s+', ' ', line)
            line = line.strip().rstrip()
            res = line.split(' ', 6)
            pathname = ''
            if len(res) == 7:
                rng, perms, offset, dev, inode, pathname, tag = res
                pathname = '{} {}'.format(pathname, tag)
            elif len(res) == 6:
                rng, perms, offset, dev, inode, pathname = res
            else:
                rng, perms, offset, dev, inode = res
            yield rng, perms, offset, dev, inode, pathname


def collect_process_stats(pid):
    stats = dict()
    stats['anonymous'] = list()
    stats['code'] = list()
    stats['data'] = list()
    stats['guard'] = list()
    stats['heap'] = list()
    stats['stack'] = list()
    stats['kernel_shared'] = list()

    for rng, perms, _, _, _, pathname in maps_lines("/proc/{}/maps".format(pid)):
        entry = dict()
        pathname.strip()
        start,stop = rng.split('-')
        entry['size_kb'] = (int(stop, 16) - int(start, 16)) / 1024
        entry['is_shared'] = 's' in perms
        entry['is_exe'] = 'x' in perms

        # Now we need to determine where we want to classify this entry, if it is file mapped
        # and the path contains /lib/ or /bin/ or the executable bit is set it is code
        # otherwise it is data.

        if pathname == '':
            stats['anonymous'].append(entry)
        elif perms == '---p' or perms == '---s':
            stats['guard'].append(entry)
        elif '/lib/' in pathname or '/bin/' in pathname or entry['is_exe']:
            stats['code'].append(entry)
        elif pathname == '[stack]':
            stats['stack'].append(entry)
        elif pathname == '[heap]':
            stats['heap'].append(entry)
        elif '[v' in pathname:
            stats['kernel_shared'].append(entry)
        else:
            stats['data'].append(entry)

    return stats


def get_stats_by_name(process_name):
    stats = dict()
    stats['counts'] = list()
    stats['anonymous'] = list()
    stats['code'] = list()
    stats['data'] = list()
    stats['guard'] = list()
    stats['heap'] = list()
    stats['stack'] = list()
    stats['kernel_shared'] = list()

    for proc in psutil.process_iter():
        if process_name in proc.name():
            count = 0
            results = collect_process_stats(proc.pid)
            for k,v in results.items():
                count += len(v)
                stats[k].extend(v)
            stats['counts'].append(count)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Collect stats on /proc/pid/maps for a given process name")
    parser.add_argument('--process', type=str, required=True, help="The process name to target")
    parser.add_argument('--output', help='Output file name, will default to process name.json', default=None)
    args = parser.parse_args(sys.argv[1:])
    out = '{}.json'.format(args.process)

    stats = get_stats_by_name(args.process)
    if args.output:
        out = args.output
    with open(out, 'w') as fd:
        json.dump(stats, fd, indent=2)


if __name__ == "__main__":
    main()

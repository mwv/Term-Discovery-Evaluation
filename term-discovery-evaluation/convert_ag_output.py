#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: mark2bogdan.py
# date: Tue March 18 12:05 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""convert mark's output to bogdan's spec for evaluation

"""

from __future__ import division

import re
from itertools import izip_longest
from collections import defaultdict

import corpus


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


def parseinputfile(fname):
    """Parse 'gold' input files that were sent to Mark.

    The input is a file with on each line:
    <file_id> phon_0 [interval0] phon_1 [interval1] (word0 [wordinterval0]) ...

    The functions yields (file_id, phones, intervals) triples,
    one for each line in the input

    :param fname: string filename
    """
    parens_pattern = re.compile(r" \((.*?)\)")
    for line in open(fname, 'r'):
        chunks = re.sub(parens_pattern, "", line).strip().split(' ')
        file_id = chunks[0]
        p = [(x[0],
              corpus.Interval(float(x[1][1:-1]),
                              float(x[2][:-1])))
             for x in grouper(chunks[1:], 3)]
        try:
            phones, intervals = zip(*p)
        except ValueError:
            phones, intervals = (None, None)
        yield (file_id, phones, intervals)


def align_chunks(chunks, phones):
    """Align parsed mark output file with parsed mark input file
    """
    chunk_idx = 0
    phon_start = 0
    chunk = ''
    for i, phon in enumerate(phones):
        chunk += phon
        if chunk == chunks[chunk_idx]:
            chunk_idx += 1
            chunk = ''
            yield (phon_start, i+1)
            phon_start = i+1


def create_classes(chunks, plist):
    output = {}
    for idx in xrange(len(chunks)):
        markline = chunks[idx]
        try:
            file_id, phones, intervals = plist[idx]
        except ValueError as e:
            print idx, phones[idx][0]
            raise e
        a = align_chunks(markline, phones)
        output[file_id] = [(markline[i],
                            corpus.Interval(intervals[start].start,
                                            intervals[stop-1].end))
                           for i, (start, stop) in enumerate(a)]
    classes = defaultdict(list)
    for file_id in output:
        for chunk, interval in output[file_id]:
            classes[chunk].append((file_id, interval))
    return classes


def write_classes(classes, outfile):
    with open(outfile, 'w') as fid:
        for class_no, chunk in enumerate(sorted(classes.keys())):
            fid.write('Class {0}\n'.format(class_no))
            for file_id, interval in classes[chunk]:
                fid.write('{0} {1:.5f} {2:.5f}\n'.format(file_id.split('_')[0],
                                                         interval.start,
                                                         interval.end))
            fid.write('\n')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print """Usage:
convert_ag_output.py <markoutput> <markinput> <classesoutputfile>"""
        exit()
    markoutput = sys.argv[1]
    markinput = sys.argv[2]
    outfile = sys.argv[3]
    print markoutput, markinput, outfile
    chunks = []
    for line in open(markoutput):
        chunks.append(line.strip().split(' '))

    phones = list(parseinputfile(markinput))
    classes = create_classes(chunks, phones)
    write_classes(classes, outfile)

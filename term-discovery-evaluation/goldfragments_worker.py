#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: goldfragments.py
# date: Tue March 18 17:13 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""goldfragments:

"""

from __future__ import division

import os
import os.path as path
import cPickle as pickle
from itertools import combinations, islice, chain, tee, izip
from collections import defaultdict

import numpy as np

from cacss import allcommonsubstrings
import corpus


CHUNKSIZE = 10000000

outdir = path.join(os.environ['HOME'], 'data', 'output',
                   'lrec_buckeye', 'goldcorrected')
try:
    os.makedirs(outdir)
except OSError:
    pass

with open('phondict.pkl', 'rb') as fid:
    phon2idx = pickle.load(fid)
idx2phon = {v: k for k, v in phon2idx.iteritems()}

phondir = corpus.phncorrecteddir

goldfile = path.join(os.environ['HOME'], 'data', 'output',
                     'lrec_buckeye', 'phon', 'phongoldcorrected.pkl')

with open(goldfile, 'rb') as fid:
    gold = pickle.load(fid)


def run(chunkstart):
    r = defaultdict(list)
    for plist1, plist2 in islice(chain(combinations(gold, 2),
                                       izip(*tee(gold, 2))),
                                 chunkstart, chunkstart+CHUNKSIZE):
        fname1, phones1, intervals1 = plist1
        fname2, phones2, intervals2 = plist2
        phones1_ = np.array([phon2idx[p] for p in phones1])
        phones2_ = np.array([phon2idx[p] for p in phones2])
        if fname1 == fname2:
            same = 1
        else:
            same = 0
        alignments = allcommonsubstrings(phones1_, phones2_, 3, same=same)
        if alignments is None:
            continue
        for row in alignments:
            r[(fname1, fname2)].append((phones1[row[0]: row[0] + row[2]],
                                        corpus.Interval(intervals1[row[0]]
                                                        .start,
                                                        intervals1[row[0] +
                                                                   row[2]-1]
                                                        .end),
                                        corpus.Interval(intervals2[row[1]]
                                                        .start,
                                                        intervals2[row[1] +
                                                                   row[2]-1]
                                                        .end)))
    return r


def write(align_dict, outfile):
    with open(outfile, 'w') as fid:
        for fname1, fname2 in sorted(align_dict.keys()):
            fid.write(fname1 + '\n')
            fid.write(fname2 + '\n')
            for a in align_dict[(fname1, fname2)]:
                fid.write('  {0} {1} {2} {3} {4}\n'.format(
                    '-'.join(a[0]),
                    a[1].start,
                    a[1].end,
                    a[2].start,
                    a[2].end))
            fid.write('\n')


if __name__ == '__main__':
    task_id = int(os.getenv('SGE_TASK_ID'))
    r = run((task_id-1) * CHUNKSIZE)
    outfile = path.join(outdir, 'gold_chunk_{0}.txt'.format(task_id))
    write(r, outfile)

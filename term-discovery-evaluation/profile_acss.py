#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: profile_acss.py
# date: Tue March 04 22:25 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""profile_acss: profile the acss module

"""

from __future__ import division
import os
import os.path as path
import cPickle as pickle
import numpy as np
from itertools import combinations
import acss
import cacss
import pstats
import cProfile


def make_profile_set(n):
    phongold = path.join(os.environ['HOME'], 'data', 'output',
                         'lrec_buckeye', 'phon', 'phongold.pkl')
    with open(phongold, 'rb') as fid:
        phongold = pickle.load(fid)
    with open(path.join(os.environ['HOME'], 'data', 'output',
                        'lrec_buckeye', 'phon', 'phongold_profileset.pkl'),
              'wb') as fid:
        plists = [(p[0],  # filename
                   zip(*reduce(lambda x, y: x+y, zip(*p[1])[2]))[0],  # phones
                   zip(*reduce(lambda x, y: x+y, zip(*p[1])[2]))[1])  # interva
                  for p in phongold[:n]]
        pickle.dump(plists, fid, -1)


def plists_to_numpy(plists):
    s = set()
    for fname, phones, intervals in plists:
        s.update(phones)
    s = sorted(list(s))
    phone2idx = dict(zip(s, range(len(s))))
    idx2phone = dict(zip(range(len(s)), s))
    r = []
    for fname, phones, intervals in plists:
        phones = np.fromiter((phone2idx[p] for p in phones), dtype=np.int)
        r.append((fname, phones, intervals))
    return r, phone2idx, idx2phone


def extract(plists):
    for i, (idx1, idx2) in enumerate(combinations(xrange(len(plists)), r=2)):
        fname1, phones1, intervals1 = plists[idx1]
        fname2, phones2, intervals2 = plists[idx2]
        cacss.allcommonsubstrings(phones1, phones2, minlength=3)


if __name__ == '__main__':
    # make_profile_set(1000)
    with open(path.join(os.environ['HOME'], 'data', 'output',
                        'lrec_buckeye', 'phon', 'phongold_profileset.pkl'),
              'rb') as fid:
        plists = pickle.load(fid)
    plists, phon2idx, idx2phon = plists_to_numpy(plists)
    cProfile.runctx('extract(plists)', globals(), locals(),
                    "cacss_profile_2.prof")
    s = pstats.Stats("cacss_profile_2.prof")
    s.strip_dirs().sort_stats("time").print_stats()

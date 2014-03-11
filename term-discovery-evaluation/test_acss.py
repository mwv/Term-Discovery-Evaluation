#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: test_acss.py
# date: Thu March 06 00:25 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""test_acss:

"""

from __future__ import division

import os
import os.path as path
import corpus
import numpy as np
import util
import acss
import cacss


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


def load_phones(f):
    r = []
    for line in open(f):
        line = [x for x in line.strip().split('\t') if x != '']
        try:
            r.append((line[2], corpus.Interval(float(line[0]),
                                               float(line[1]))))
        except IndexError as e:
            print f
            print line
            raise e
    return r


if __name__ == '__main__':
    files = list(util.rglob('/home/mwv/projects/term-discovery-evaluation/'
                            'tests/mockphones/', '*.phones'))
    plists = [(path.basename(f),
               zip(*load_phones(f))[0],
               zip(*load_phones(f))[1]) for f in files]
    r, phone2idx, idx2phone = plists_to_numpy(plists)
    _, phones1, _ = r[0]
    _, phones2, _ = r[1]
    r1 = acss.allcommonsubstrings(phones1, phones2, 3)
    r2 = cacss.allcommonsubstrings(phones1, phones2, 3)
    PASS = 'TEST PASSED'
    FAIL = 'TEST FAILED'
    if len(r1) != len(r2):
        print 'unequal number of returned alignments: {0}, {1}'.format(
            len(r1), len(r2))
        print FAIL
        exit()
    for align1, inds1 in r1:
        for align2, inds2 in r2:
            if np.array_equal(align1, align2) and \
               inds1[0][0] == inds2[0][0] and inds1[0][-1] == inds2[0][-1] and \
               inds1[1][0] == inds2[1][0] and inds1[1][-1] == inds2[1][-1]:
                break
        else:
            print 'unequal alignments.'
            print FAIL
            exit()
    # for idx in range(len(r1)):
    #     align1, inds1 = r1[idx]
    #     align2, inds2 = r2[idx]
    #     if not np.array_equal(align1, align2):
    #         print 'alignment {0} does not match: {1}, {2}'.format(
    #             idx, align1, align2)
    #         print FAIL
    #         exit()
    #     print inds1
    #     print inds2
    #     if inds1[0][0] != inds2[0][0] or inds1[0][-1] != inds2[0][-1] or \
    #        inds1[1][0] != inds2[1][0] or inds1[0][-1] != inds2[0][-1]:
    #         print 'index {0} does not match: {1}, {2}'.format(
    #             idx, inds1, inds2)
    #         print
    #         print r1
    #         print
    #         print r2
    #         print FAIL
    #         exit()
    print PASS

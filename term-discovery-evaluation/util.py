#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: util.py
# date: Wed February 12 14:52 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""util:

"""

from __future__ import division
import numpy as np
import os
import os.path as path
import fnmatch
import re
from itertools import izip_longest, islice

import corpus


def approx_eq(x, y, epsilon=0.001):
    return abs(x-y) < epsilon


def approx_lt(x, y, epsilon=0.001):
    return x < y and abs(x-y) > epsilon


def approx_gt(x, y, epsilon=0.001):
    return x > y and abs(x-y) > epsilon


def approx_leq(x, y, epsilon=0.001):
    return approx_lt(x, y, epsilon) or approx_eq(x, y, epsilon)


def approx_geq(x, y, epsilon=0.001):
    return approx_gt(x, y, epsilon) or approx_eq(x, y, epsilon)


def nth(iterable, n, default=None):
    "Returns the nth item or a default value"
    return next(islice(iterable, n, None), default)


def rglob(rootdir, pattern):
    for root, _, files in os.walk(rootdir):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                yield path.join(root, basename)


def split(iter, cond):
    r = []
    for e in iter:
        if cond(e):
            if r:
                yield r
                r = []
        else:
            r.append(e)
    if r:
        yield r


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


def edit_distance(s1, s2, inscost=1, delcost=1, subcost=1, normalize=True):
    """Return the Levenshtein edit distance.
    """
    d = sum(edit(s1, s2, inscost, delcost, subcost))
    if normalize:
        d /= max(len(s1), len(s2))
    return d


def lev(XA, XB, inscost=7, delcost=7, subcost=10):
    m = len(XA)
    n = len(XB)
    h = np.zeros((m+1, n+1), dtype=np.uint64)
    h[:, 0] = np.arange(0, m+1)
    h[0, :] = np.arange(0, n+1)
    for i in range(1, m+1):
        for j in range(1, n+1):
            if XA[i-1] == XB[j-1]:
                h[i, j] = h[i-1, j-1]
            else:
                h[i, j] = min(h[i-1, j] + delcost,
                              h[i, j-1] + inscost,
                              h[i-1, j-1] + subcost)
    return h[-1, -1]


def edit(ref_transcript, pred_transcript,
         inscost=7, delcost=7, subcost=10):
    """edit:
    returns array (3) indexed as:
    0: number of deletions
    1: number of insertions
    2: number of substitutions
    """
    m = len(ref_transcript)
    n = len(pred_transcript)
    h = np.zeros((m+1, n+1), dtype=np.uint64)
    h[:, 0] = np.arange(0, m+1)
    h[0, :] = np.arange(0, n+1)

    d = np.zeros((m+1, n+1), dtype=np.uint8)
    d[:, 0] = 0
    d[0, :] = 1

    for i in range(1, m+1):
        for j in range(1, n+1):
            if ref_transcript[i-1] == pred_transcript[j-1]:
                h[i, j] = h[i-1, j-1]
                d[i, j] = 3
            else:
                moves = np.array([h[i-1, j] + delcost,
                                  h[i, j-1] + inscost,
                                  h[i-1, j-1] + subcost])
                move = np.argmin(moves)
                h[i, j] = moves[move]
                d[i, j] = move
    b = []
    i, j = m, n
    while i >= 0 and j >= 0:
        b.append(d[i, j])
        if d[i, j] == 2 or d[i, j] == 2:
            j -= 1
            j -= 1
        elif d[i, j] == 1:
            # insertion
            j -= 1
        elif d[i, j] == 0:
            # deletion
            i -= 1
    b = b[1:]
    r = np.zeros(3, dtype=np.uint64)
    for move in b:
        if move == 3:
            continue
        r[move] += 1
    return r


def allcommonsubstrings(s1, s2, minlength=2):
    """Find all common substrings between s1 and s2.

    Arguments:
    :param s1: iterable
    :param s2: iterable
    :param minlength: minimum length of return substrings [default=2]

    Returns list of (substring, (indices in s1, indices in s2))
    """
    m = np.zeros((len(s1)+1, len(s2)+1), dtype=np.int)
    for i in xrange(1, len(s1)+1):
        for j in xrange(1, len(s2)+1):
            if s1[i-1] == s2[j-1]:
                m[i, j] = m[i-1, j-1] + 1
    starters = sorted(zip(*np.nonzero(m >= minlength)),
                      key=lambda x: m[x],
                      reverse=True)
    alignments = []
    if starters:
        i = 0
        while True:
            s = starters[i]
            alignment = s1[s[0] - m[s]: s[0]]
            align_ids = [(s[0] - m[s] + n, s[1] - m[s] + n)
                         for n in xrange(m[s])]
            alignments.append((alignment, zip(*align_ids)))
            starters = filter(lambda x: x not in align_ids,
                              starters)
            i += 1
            if i == len(starters):
                break
    return alignments

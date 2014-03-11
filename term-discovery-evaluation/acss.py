#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: acss.py
# date: Fri February 28 14:11 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""acss:

"""

from __future__ import division
import numpy as np


def allcommonsubstrings(XA, XB, minlength=3):
    """Find all common substrings between s1 and s2.

    Arguments:
    :param s1: iterable
    :param s2: iterable
    :param minlength: minimum length of return substrings [default=2]

    Returns list of (substring, (indices in s1, indices in s2))
    """
    mA = XA.shape[0]
    mB = XB.shape[0]
    m = np.zeros((mA+1, mB+1), dtype=np.int)
    for i in xrange(1, mA+1):
        for j in xrange(1, mB+1):
            if XA[i-1] == XB[j-1]:
                m[i, j] = m[i-1, j-1] + 1
    starters = sorted(zip(*np.nonzero(m >= minlength)),
                      key=lambda x: m[x],
                      reverse=True)
    if len(starters) == 0:
        return []
    alignments = []
    while True:
        s = starters[0]
        alignment = XA[s[0] - m[s]: s[0]]
        align_ids = [(s[0] - m[s] + n, s[1] - m[s] + n)
                     for n in xrange(1, m[s]+1)]
        _align_ids = zip(*align_ids)
        for start in xrange(len(alignment)):
            for end in xrange(start + minlength, len(alignment)+1):
                alignments.append((alignment[start:end],
                                   (_align_ids[0][start:end],
                                    _align_ids[1][start:end])))
        starters = [x for x in starters if x not in align_ids]
        if len(starters) == 0:
            break
    return alignments

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


def allcommonsubstrings(s1, s2, minlength=3, debug=False):
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
    if debug:
        _starters = starters[:]
    if len(starters) == 0:
        return []
    alignments = []
    i = 0
    while True:
        s = starters[i]
        alignment = s1[s[0] - m[s]: s[0]]
        align_ids = [(s[0] - m[s] + n, s[1] - m[s] + n)
                     for n in xrange(m[s])]
        _align_ids = zip(*align_ids)
        for start in xrange(len(alignment)):
            for end in xrange(start + minlength, len(alignment)+1):
                alignments.append((alignment[start:end],
                                   (_align_ids[0][start:end],
                                    _align_ids[1][start:end])))
        starters = [x for x in starters if x not in align_ids]
        # starters = filter(lambda x: x not in align_ids,
        #                   starters)
        i += 1
        if i == len(starters):
            break
    if debug:
        return alignments, m, _starters
    return alignments

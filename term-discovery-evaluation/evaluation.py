#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: _evaluation.py
# date: Wed February 12 12:43 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""_evaluation:

"""

from __future__ import division
import util


def NED(discovered_fragment_indices, corpus):
    """Average normalized edit distance.

    Arguments:
    :param discovered_fragment_indices: iterable of fragment index pairs
    :param corpus: iterable of phoneme symbols
    """
    return sum(util.edit_distance(corpus[i:j+1], corpus[k:l+1])
               for ((i, j), (k, l)) in discovered_fragment_indices) / \
        len(corpus)

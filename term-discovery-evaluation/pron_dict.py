#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: pron_dict.py
# date: Wed February 26 00:29 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""pron_dict:

"""

from __future__ import division

import os
import os.path as path
from collections import defaultdict
import cPickle as pickle

import corpus

outdir = path.join(os.environ['HOME'], 'data', 'output',
                   'lrec_buckeye')
try:
    os.makedirs(outdir)
except OSError:
    pass


def build_pron_dict_single(wordslist, phoneslist):
    """Build a pronunciation dictionary from a words interval list and
    phones intervals list

    Arguments:
    :param wordslist: list of (symbol, Interval) pairs
    :param phoneslist: list of (symbol, Interval) pairs
    """
    d = defaultdict(set)
    for word, interval in wordslist:
        pron = tuple([p[0] for p in phoneslist
                      if p[1].start >= interval.start
                      and p[1].end <= interval.end])
        if len(pron):
            d[word].add(pron)
    return d


def build_pron_dict_global():
    filepairs = get_filepairs()
    pron_dict = defaultdict(set)
    for wfile, pfile in filepairs:
        plist = corpus.extract_content(pfile, 'phones')
        wlist = corpus.extract_content(wfile, 'words')
        d = build_pron_dict_single(wlist, plist)
        for word in d:
            pron_dict[word].update(d[word])
    return pron_dict


def get_filepairs():
    filepairs = []
    for pfile, wfile, _, _ in corpus.get_filesets():
        filepairs.append((wfile, pfile))
    return filepairs


if __name__ == '__main__':
    pron_dict = build_pron_dict_global()
    with open('pron_dict.txt', 'w') as fid:
        for word in sorted(pron_dict.keys()):
            fid.write(word + '\n')
            for pron in sorted(pron_dict[word]):
                fid.write(' ' + ' '.join(pron) + '\n')
    with open('pron_dict.pkl', 'wb') as fid:
        pickle.dump(pron_dict, fid, -1)

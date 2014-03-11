#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: extract_phones.py
# date: Mon February 24 15:16 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""extract_phones:

"""

from __future__ import division

import os
import os.path as path
import cPickle as pickle

import corpus
import util
from symbols import SPLITS, IGNORE

outdir = path.join(os.environ['HOME'], 'data', 'output',
                   'lrec_buckeye', 'phon')
try:
    os.makedirs(outdir)
except OSError:
    pass


def geq(x, y, epsilon=0.001):
    return x > y or abs(x-y) < epsilon


def leq(x, y, epsilon=0.001):
    return x < y or abs(x-y) < epsilon


def separate_by_line():
    """At Mark's request, format phones as:

    <FILEID> phone1 phone2 phone3 (corresponding word) phone4 ...
    """
    destfile = path.join(outdir, 'phonbyline.txt')
    destgold = path.join(outdir, 'phongold.txt')
    fidmark = open(destfile, 'w')
    fidgold = open(destgold, 'w')
    s = []
    for pfile, wfile, _, _ in sorted(corpus.get_filesets()):
        plist = corpus.extract_content(pfile, 'phones')
        psplit = util.split(plist, lambda x: x[0] in SPLITS)
        wlist = corpus.extract_content(wfile, 'words')

        rtot = []
        for pspl in psplit:
            r = []
            for word, interval in wlist:
                phones = [x for x in pspl
                          if geq(x[1].start, interval.start)
                          and leq(x[1].end, interval.end)
                          # if x[1].start >= interval.start
                          # and x[1].end <= interval.end
                          and x[0] not in IGNORE]
                if phones:
                    r.append((word, interval, phones))
            if r:
                rtot.append(r)

        basename = path.splitext(path.basename(pfile))[0]

        for idx, split in enumerate(rtot):
            fidmark.write('{f}_{i}'.format(f=basename, i=idx))
            s.append(('{f}_{i}'.format(f=basename, i=idx), split))
            for word, interval, phones in split:
                fidmark.write(' ')
                fidmark.write(' '.join(zip(*phones)[0]))
                fidmark.write(' ')
                fidmark.write('({w})'.format(w=word))
            fidmark.write('\n')

            fidgold.write('{f}_{i}'.format(f=basename, i=idx))
            for word, interval, phones in split:
                fidgold.write(' ')
                fidgold.write(' '.join('{p} {i}'.format(p=p,
                                                        i=ival)
                                       for p, ival in phones))
                fidgold.write(' ')
                fidgold.write('({w} {i})'.format(w=word,
                                                 i=interval))
            fidgold.write('\n')
    fidmark.close()
    fidgold.close()
    with open(path.join(outdir, 'phongold.pkl'), 'wb') as fid:
        pickle.dump(s, fid, -1)


if __name__ == '__main__':
    separate_by_line()

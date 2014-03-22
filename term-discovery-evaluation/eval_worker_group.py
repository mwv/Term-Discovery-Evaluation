#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: evaluation_worker.py
# date: Sat March 22 01:09 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""evaluation_worker: sge worker unit for evaluation

"""

from __future__ import division

import os
import os.path as path
from collections import defaultdict
from itertools import *


import cPickle as pickle


CHUNKSIZE = 100000


def Pclus(classdict):
    """Generate Pclus
    :param classdict: dict from class number to tuple of Fragments

    :returns generator of pairs of
      ((classno1, fragment1), (classno2, fragment2))

    """
    return (((classno, f1), (classno, f2))
            for c in classdict
            for classno, (f1, f2) in izip(repeat(c),
                                          combinations(classdict[c],
                                                       2)))


def Pgoldclus(classdict):
    """Generate Pgoldclus
    :param classdict: dict from class number to tuple of Fragments

    :returns generator of pairs of
      ((classno1, fragment1), (classno2, fragment2))
    """
    same = izip(*tee(chain(*(izip(repeat(k), v)
                             for k, v in classdict.iteritems()))))
    combos = combinations(chain(*(izip(repeat(k), v)
                                  for k, v in classdict.iteritems())),
                          2)
    return (((c1, f1), (c2, f2))
            for (c1, f1), (c2, f2) in chain(combos, same)
            if f1.phones == f2.phones
            and not (f1.fname == f2.fname and f1.interval == f2.interval))


def flatten(p):
    """flattens a set of ((c1, p1), (c2, p2)) pairs into
    an iterator of (c, p) pairs
    """
    return chain.from_iterable(p)


def nmatch(pset):
    """Return a dict from phonseq to int, where int is the number of
    times the phonseq occurs in flatten(pset)

    Arguments:
    :param pset: set of ((c1, p1), (c2, p2)) pairs
    """
    d = defaultdict(int)
    for _, fragment in flatten(pset):
        d[fragment.phones] += 1
    return d


def weight(phonseq, cts):
    """Returns relative frequency of phonseq, according to counts"""
    return cts[phonseq] / sum(cts.values())


def counts(p):
    """returns dict from phonseq to count

    :param p: set of ((c1, p1), (c2, p2)) pairs

    """
    # phoneset = set(x[1].phones for x in flatten(p))
    # d = {x: 0 for x in phoneset}
    d = defaultdict(int)
    for (_, p1), (_, p2) in p:
        d[p1.phones] += 1
        d[p2.phones] += 1
    return d


def evaluate_group(clsdict, typeset, chunkstart):
    intersection = (p for p in Pclus(clsdict)
                    if p[0][1].phones == p[1][1].phones)
    nm_pclus = nmatch(Pclus(clsdict))
    nm_pgoldclus = nmatch(Pgoldclus(clsdict))
    nm_inters = nmatch(intersection)

    cts = counts(Pclus(clsdict))
    total = sum(cts.values())

    precision = 0.0
    recall = 0.0
    for t in typeset[chunkstart: chunkstart + CHUNKSIZE]:
        inters_nm = nm_inters[t]
        pclus_nm = nm_pclus[t]
        pgoldclus_nm = nm_pgoldclus[t]

        w = cts[t] / total
        if pclus_nm > 0:
            precision += w * inters_nm / pclus_nm
        if pgoldclus_nmatch > 0:
            recall += w * inters_nm / pgoldclus_nm
    return precision, recall


if __name__ == '__main__':
    resultdir = path.join(os.environ['HOME'], 'data', 'output',
                          'lrec_buckeye', 'results', 'formatted_output')
    taskname = os.getenv('LREC_EVAL_TASKNAME')

    clsdictfile = path.join(resultdir, taskname + '_clsdict.pkl')
    with open(clsdictfile, 'rb') as fid:
        clsdict = pickle.load(fid)

    typesetfile = path.join(resultdir, taskname + '_typeset.pkl')
    with open(typesetfile, 'rb') as fid:
        typeset = sorted(list(pickle.load(fid)))

    sge_id = int(os.getenv('SGE_TASK_ID'))
    chunkstart = (sge_id - 1) * CHUNKSIZE

    outdir = path.join(os.environ['HOME'], 'data', 'output',
                       'lrec_buckeye', 'scores', taskname)
    try:
        os.makedirs(outdir)
    except OSError:
        pass
    outfile = path.join(outdir, 'chunk_{0}'.format(sge_id))
    precision, recall = evaluate_group(clsdict, typeset, chunkstart)
    with open(outfile, 'w') as fid:
        fid.write('{0:.10f} {1:.10f}'.format(precision, recall))

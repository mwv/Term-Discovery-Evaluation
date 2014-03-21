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

import os
import os.path as path
import re
import time
from collections import defaultdict
from itertools import *
import glob
from collections import namedtuple
import cPickle as pickle
from operator import itemgetter

import corpus
from corpus import Interval, Fragment
from util import approx_lt, approx_gt, approx_geq
import util


def load_classfile(fname, phonfiledict):
    """Load class file (output from discovery system

    :param fname: filename

    returns:
    :param r: dict from class number to tuple of Fragments
      (filename, phoneseq, interval) pairs)
    """
    classp = re.compile(r"Class (?P<class_number>\d+)")
    r = {}
    curr = []
    curr_class = None
    for lineno, line in enumerate(open(fname, 'r')):
        m = re.match(classp, line)
        if m:  # on a line with a class label
            if curr_class is None:
                curr_class = int(m.group('class_number'))
            else:
                raise ValueError('new class while reading class')
        else:  # on an interval line or a whitespace line
            if len(line.strip()) > 0:
                split = line.strip().split(' ')
                curr.append((split[0], Interval(float(split[1]),
                                                float(split[2]))))
            else:  # whitespace line, reset
                if curr_class is None:
                    if lineno == 0:
                        continue
                    print lineno, line
                    raise ValueError('attempting to end reading class '
                                     'while not reading class in line {0}'
                                     .format(lineno))
                r[curr_class] = curr
                curr = []
                curr_class = None
    r_ = defaultdict(list)
    for c, v in r.iteritems():
        for x in v:
            fname = x[0]
            interval = x[1]
            try:
                annot, intervals = zip(*get_annotation(fname.split('_')[0],
                                                       interval,
                                                       phonfiledict))
            except ValueError:
                continue
            total_silence = 0.0
            for i in range(len(annot)):
                if annot[i] == '__':
                    total_silence += intervals[i].end - intervals[i].start
            if total_silence > 0.5 * (intervals[-1].end - intervals[0].start):
                continue
            elif total_silence > 0.0:
                a = []
                for i in annot:
                    if i != '__':
                        a.append(i)
                annot = a
            if annot != []:
                r_[c].append(Fragment(fname, tuple(annot), interval))
    r = {c: tuple(v) for c, v in r_.iteritems()}
    return r


def allsubstrings(a, minlength=3):
    for start, end in combinations(xrange(len(a)), 2):
        if end - start > minlength - 2:
            yield a[start: end + 1]


def substring_pair(pair, phonfiledict):
    """Return the substring completion of pair ((c1, p1), (c2, p2))
    """
    (c1, fragment1), (c2, fragment2) = pair
    fname1 = fragment1.fname
    fname2 = fragment2.fname
    phones1 = fragment1.phones
    phones2 = fragment2.phones
    intervals1 = tuple(get_intervals(fragment1.fname, fragment1.interval,
                                     phonfiledict))
    intervals2 = tuple(get_intervals(fragment2.fname, fragment2.interval,
                                     phonfiledict))
    for seq1, seq2 in product(allsubstrings(zip(phones1, intervals1), 3),
                              allsubstrings(zip(phones2, intervals2), 3)):
        phonseq1, ivalseq1 = zip(*seq1)
        phonseq2, ivalseq2 = zip(*seq2)
        interval1 = Interval(ivalseq1[0].start, ivalseq2[-1].end)
        interval2 = Interval(ivalseq2[0].start, ivalseq2[-1].end)
        yield ((c1, Fragment(fname1, tuple(phonseq1), interval1)),
               (c2, Fragment(fname2, tuple(phonseq2), interval2)))


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


def Psubs(classdict, phonfiledict):
    """Generate Psubs

    Arguments:
    :param classdict: dict from class number to tuple of Fragments
    :

    :returns generator of pairs of
      ((classno1, fragment1), (classno2, fragment2))
    """
    return chain.from_iterable(substring_pair(pair, phonfiledict)
                               for pair in Pclus(classdict))


def Pgold(classdict):
    return Pclus(classdict)


def check_overlap(ref_interval, phon_interval):
    """Return True iff the ref_interval overlaps at least half
    of the phon_interval and the overlap is at least 0.03 seconds

    :param phon_interval: Interval
    :param ref_interval: Interval
    """
    if approx_lt(phon_interval.end, ref_interval.start):
        return False
    if approx_gt(phon_interval.start, ref_interval.end):
        return False
    overlap = min(phon_interval.end, ref_interval.end) - \
        max(phon_interval.start, ref_interval.start)

    return approx_geq(overlap, 0.03) and \
        approx_geq(overlap, 0.5 * (phon_interval.end - phon_interval.start))


__annot_memo = {}


def get_annotation(fname, interval, phonfiledict, foldphones=True):
    # if not (fname, interval, foldphones) in __annot_memo:
    nopre = dropwhile(lambda x: not check_overlap(interval, x[1]),
                      phonfiledict[fname])
    nopost = takewhile(lambda x: check_overlap(interval, x[1]),
                       nopre)
        # __annot_memo[(fname, interval, foldphones)] = \
    return [(corpus.fold(x[0]), x[1]) if foldphones else x
            for x in nopost]
    # return __annot_memo[(fname, interval, foldphones)]


def get_intervals(fname, interval, phonfiledict):
    return imap(itemgetter(1),
                get_annotation(fname, interval, phonfiledict))


def get_phones(fname, interval, phonfiledict, foldphones=True):
    """Return the phonemic annotation string matching the interval in fname.
    """
    return imap(itemgetter(0),
                get_annotation(fname, interval, phonfiledict, foldphones))


def load_phonfiledict():
    """Return a dict from filenames to list of (phone, interval) pairs
    """
    d = {}
    for f in glob.iglob(path.join(corpus.phncorrecteddir, '*.phn')):
        bname = path.splitext(path.basename(f))[0]
        d[bname] = corpus.extract_content(f, 'phones')
    return d


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


def evaluate_group(classdict, phonfiledict):
    intersection = (p for p in Pclus(classdict)         if p[0][1].phones == p[1][1].phones)

    nm_pclus = nmatch(Pclus(classdict))
    nm_pgoldclus = nmatch(Pgoldclus(classdict))
    nm_intersection = nmatch(intersection)
    cts = counts(Pclus(classdict))
    precision = 0.0
    recall = 0.0
    typeset = set(x[1].phones for x in flatten(Pclus(classdict)))
    for idx, t in enumerate(typeset):
        intersection_nmatch = nm_intersection[t]
        pclus_nmatch = nm_pclus[t]
        pgoldclus_nmatch = nm_pgoldclus[t]

        w = weight(t, cts)
        if pclus_nmatch > 0:
            precision += w * intersection_nmatch / pclus_nmatch
        if pgoldclus_nmatch > 0:
            recall += w * intersection_nmatch / pgoldclus_nmatch
    return (2 * precision * recall) / (precision + recall), precision, recall


def evaluate_matching(disc_classdict, gold_classdict, phonfiledict):
    t0 = time.time()
    print 'calculating intersection...',
    intersection = set(p for p in Psubs(disc_classdict, phonfiledict)
                       if p in Pclus(gold_classdict))
    print 'done. time: {0:.3f}s'.format(time.time() - t0)
    # intersection = set(Psubs(disc_classdict, phonfiledict)) & set(Pclus(gold_classdict))
    nmatch_disc = nmatch(Psubs(disc_classdict, phonfiledict))
    nmatch_gold = nmatch(Pgold(gold_classdict))
    nmatch_intersection = nmatch(intersection)

    cts = counts(Psubs(disc_classdict, phonfiledict))
    precision = 0.0
    recall = 0.0

    typeset = set(x[1].phones for x in flatten(Psubs(disc_classdict,
                                                     phonfiledict)))
    for idx, t in enumerate(typeset):
        intersection_nmatch = nmatch_intersection[t]
        psubs_nmatch = nmatch_disc[t]
        pgold_nmatch = nmatch_gold[t]

        w = weight(t, cts)
        if psubs_nmatch > 0:
            precision += w * intersection_nmatch / psubs_nmatch
        if pgold_nmatch > 0:
            recall += w * intersection_nmatch / pgold_nmatch
    return (2 * precision * recall) / (precision + recall), precision, recall


def weight(phonseq, cts):
    """Returns relative frequency of phonseq, according to counts"""
    return cts[phonseq] / sum(cts.values())


def flatten(p):
    """flattens a set of ((c1, p1), (c2, p2)) pairs into
    an iterator of (c, p) pairs
    """
    return chain.from_iterable(p)


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


def evaluate(set1, set2, ind1, ind2, flat_set1, intersection):
    typ = types(set1)
    precision = 0.0
    recall = 0.0
    fscore = 0.0
    #print typ
    for t in typ:
        w = weight(t, flat_set1)
        # inters = intersection(set1, set2, ind1, ind2)
        #print inters
        match_inters = match(t, inters)
        #print t, w, match_inters
        m1 = match(t, set1)
        m2 = match(t, set2)
        if (m1 != 0):
            precision += w * match_inters / m1
        if (m2 != 0):
            recall += w * match_inters / m2
    if (precision + recall != 0):
        fscore = (2 * precision * recall) / (precision + recall)
    return precision, recall, fscore


if __name__ == '__main__':
    import sys
    discclassfile = sys.argv[1]
    t0 = time.time()
    # discclassfile = '/home/mwv/data/output/lrec_buckeye/bogdan/aren_15D'
    goldclassfile = '/home/mwv/data/output/lrec_buckeye/goldcorrected.cls'

    print 'loading phonfiledict...',
    phonfiledict = load_phonfiledict()
    print 'done. time: {0:.3f}s'.format(time.time() - t0)

    t0 = time.time()
    print 'loading disc class file...',
    discclassdict = load_classfile(discclassfile, phonfiledict)
    # with open('classdict.pkl', 'rb') as fid:
    #     classdict = pickle.load(fid)
    print 'done. time: {0:.3f}s'.format(time.time() - t0)

    # t0 = time.time()
    # print 'loading gold class file...',
    # # goldclassdict = load_classfile(goldclassfile, phonfiledict)
    # with open('goldclassdict.pkl', 'rb') as fid:
    #     goldclassdict = pickle.load(fid)
    # print 'done. time: {0:.3f}s'.format(time.time() - t0)

    # with open('goldclassdict.pkl', 'wb') as fid:
    #     pickle.dump(goldclassdict, fid, -1)

    # t0 = time.time()
    # print 'constructing Pclus...',
    # pclus = Pclus(classdict)
    # print 'done. time: {0:.3f}s'.format(time.time() - t0)

    # t0 = time.time()
    # print 'constructing Pgoldclus...',
    # pgoldclus = Pgoldclus(classdict)
    # print 'done. time: {0:.3f}s'.format(time.time() - t0)

    t0 = time.time()
    print 'evaluating group f-score...',
    # fscore, precision, recall = evaluate_matching(discclassdict, goldclassdict, phonfiledict)
    fscore, precision, recall = evaluate_group(discclassdict, phonfiledict)
    print 'time: {0:.3f}s'.format(time.time() - t0)

    print fscore, precision, recall

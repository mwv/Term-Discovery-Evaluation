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
from collections import defaultdict

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


def format_phonrec():
    # load up the phone recognizer files
    phonrecdir = path.join(os.environ['HOME'],
                           'data/output/lrec_buckeye/phonrecoutput',
                           'res_tri200_simple_S_bigr/')
    phonrecinput = path.join(phonrecdir, 'refTranscriptions.mlf')
    phonrecoutput = path.join(phonrecdir, 'modelTranscriptions.mlf')
    prinput = corpus.readmlf(phonrecinput)
    proutput = corpus.readmlf(phonrecoutput)
    # index the input and output by filename
    prinput = {x[0]: (x[1], x[2])
               for x in prinput}
    proutput = {x[0]: (x[1], x[2])
                for x in proutput}

    # load up the gold transcriptions
    # with open(path.join(outdir, 'phongold.pkl'), 'rb') as fid:
    #     gold = pickle.load(fid)

    # build dict from fname to phoneseq to start time
    phondict = defaultdict(dict)
    worddict = defaultdict(list)
    # for e in gold:
    #     fname = e[0].split('_')[0]
    #     phonseq = tuple(map(corpus.fold, reduce(lambda x, y: x+y,
    #                                             (zip(*p)[0]
    #                                              for p in zip(*e[1])[2]))))
    #     start_time = e[1][0][1].start
    #     phondict[fname][phonseq] = start_time

    #     for word, interval in zip(zip(*e[1])[0], zip(*e[1])[1]):
    #         worddict[fname].append((word, interval))
    for pfile, wfile, _, _ in corpus.get_filesets():
        fname = path.splitext(path.basename(pfile))[0]
        plist = corpus.extract_content(pfile, 'phones', True)
        for s in util.split(plist, lambda x: x[0] == '__'):
            if s == []:
                continue
            phonseq, intervals = zip(*s)
            phondict[fname][tuple(phonseq)] = intervals[0].start

        wlist = corpus.extract_content(wfile, 'words')
        for word, interval in wlist:
            worddict[fname].append((word, interval))
    ns2sec = 0.0000001

    markfile = path.join(outdir, 'phonrec.txt')
    goldfile = path.join(outdir, 'phonrecgold.txt')
    fidmark = open(markfile, 'w')
    fidgold = open(goldfile, 'w')
    # now line them up
    rtot = []
    missing = 0
    for fname in sorted(proutput.keys()):
        bname = fname.split('_')[0]
        gold_phones, _ = prinput[fname]
        pred_phones, pred_intervals = proutput[fname]
        start_time = phondict[bname][tuple(gold_phones)]
        pred_intervals = [corpus.Interval(start_time + i.start * ns2sec,
                                          start_time + i.end * ns2sec)
                          for i in pred_intervals]

        words, word_intervals = zip(*worddict[bname])
        wrd_idx = 0
        phn_idx = 0
        # find the starting word
        for i in range(0, len(words)):
            if geq(word_intervals[i].end, pred_intervals[phn_idx].start) \
               and leq(word_intervals[i].start, pred_intervals[phn_idx].end):
                wrd_idx = i
                break
        else:
            for word, interval in zip(words, word_intervals):
                print interval, word
            print 'PHN:', pred_intervals[phn_idx]
            print fname
            print start_time
            raise ValueError('no suitable word interval found')
        r = [(words[wrd_idx], word_intervals[wrd_idx], [])]
        r_idx = 0
        while phn_idx < len(pred_phones):
            if leq(word_intervals[wrd_idx].end, pred_intervals[phn_idx].end):
                wrd_idx += 1
                if wrd_idx >= len(words):
                    break
                r.append((words[wrd_idx], word_intervals[wrd_idx], []))
                r_idx += 1
            r[r_idx][2].append((pred_phones[phn_idx], pred_intervals[phn_idx]))
            phn_idx += 1
        rtot.append(r)

        fidmark.write(fname)
        for word, interval, plist in r:
            if plist == []:
                continue
            fidmark.write(' ')
            fidmark.write(' '.join(zip(*plist)[0]))
            fidmark.write(' ')
            fidmark.write('({w})'.format(w=word))
        fidmark.write('\n')

        fidgold.write(fname)
        for word, interval, plist in r:
            if plist == []:
                continue
            fidgold.write(' ')
            fidgold.write(' '.join('{p} {i}'.format(p=p,
                                                    i=ival)
                                   for p, ival in plist))
            fidgold.write(' ')
            fidgold.write('({w} {i})'.format(w=word,
                                             i=interval))
        fidgold.write('\n')
    fidmark.close()
    fidgold.close()
    with open(path.join(outdir, 'phonrecoutgold.pkl'), 'wb') as fid:
        pickle.dump(rtot, fid, -1)
    print 'MISSING:', missing


if __name__ == '__main__':
    format_phonrec()

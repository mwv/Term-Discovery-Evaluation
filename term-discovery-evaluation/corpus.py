#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: corpus.py
# date: Wed February 26 21:29 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""corpus: interface functions to the transcriptions of the buckeye corpus

"""

from __future__ import division

import os
import os.path as path
from re import compile, match
from collections import namedtuple
import json

import util

datadir = path.join(os.environ['HOME'],
                    'data', 'BUCKEYE')
phncorrecteddir = path.join(os.environ['HOME'], 'data', 'output',
                            'lrec_buckeye', 'phon_corrected', 'phn')

__phonesp = compile(r"^ *(?P<end>\d+(?:\.\d*)?|\.\d+) +\d+ +(?P<symbol>.+)$")
__wordsp = compile(r"^ *(?P<end>\d+(?:\.\d*)?|\.\d+)"
                   " +\d+ +(?P<symbol>.+?);.*$")
__triphonep = compile(r"^(?P<pre>.+?)-(?P<symbol>.+?)\+(?P<post>.+?)$")
Interval = namedtuple('Interval', ['start', 'end'])
Interval.__repr__ = lambda x: '[{0}, {1}]'.format(x.start, x.end)
FileSet = namedtuple('FileSet', ['phones', 'words', 'txt', 'wav'])
Fragment = namedtuple('Fragment', ['fname', 'phones', 'interval'])

with open('buckeye_foldings.json') as fid:
    __fold = json.load(fid)


def parse_goldfile(f):
    curr_fname1 = None
    curr_fname2 = None
    curr_fragments = []
    for line in open(f):
        if line.startswith('s'):
            if curr_fname1 is None:
                curr_fname1 = line.strip()
            elif curr_fname2 is None:
                curr_fname2 = line.strip()
            else:
                raise ValueError('attempting to read filename while filenames'
                                 ' have already been read.')
        elif line.strip() == '':
            for fragment in curr_fragments:
                yield fragment
            curr_fname1 = None
            curr_fname2 = None
            curr_fragments = []
        else:
            if curr_fname1 is None or curr_fname2 is None:
                raise ValueError('attempting to read intervals while'
                                 ' filenames are None')
            s = line.strip().split(' ')
            phonseq = tuple(s[0].split('-'))
            interval1 = Interval(float(s[1]), float(s[2]))
            interval2 = Interval(float(s[3]), float(s[4]))
            curr_fragments.append(Fragment(curr_fname1,
                                           phonseq,
                                           interval1))
            curr_fragments.append(Fragment(curr_fname2,
                                           phonseq,
                                           interval2))
    for fragment in curr_fragments:
        yield fragment


def readmlf(fname):
    """Read triphone mlf"""
    result = []
    current_intervals = None
    current_symbols = None
    current_fname = None
    current_contexts = None
    in_file = False
    for line in open(fname):
        if line.startswith('"'):
            current_fname = line.strip().split('/')[1].split('.')[0]
            in_file = True
            current_intervals = []
            current_symbols = []
            current_contexts = []
            continue
        elif line.startswith('<s>'):
            # just ignore
            continue
        elif (line.startswith('</s>')
              or line.startswith('#!MLF!#')):
            # just ignore
            continue
        elif line.startswith('.'):
            result.append((current_fname, current_symbols,
                           current_intervals, current_contexts))
            current_fname = None
            current_symbols = None
            current_intervals = None
            current_contexts = None
            in_file = False
            continue
        elif not in_file:
            raise ValueError('error parsing line: {0}'.format(line))
        # now we are in_file and parsing interval lines
        line = line.strip().split()
        current_intervals.append(Interval(int(line[0]), int(line[1])))
        m = match(__triphonep, line[2])
        if m is None:
            continue
        symbol = m.group('symbol')
        current_symbols.append(symbol)
        pre = m.group('pre')
        post = m.group('post')
        current_contexts.append((pre, post))
    return result


def extract_content(filename, filetype, foldphones=False):
    """For txt files, return a list of utterances.
    For phones and words files, return a list of (symbol, Interval) pairs.

    Arguments:
    :param filename: filename
    :param filetype: must be one of 'phones', 'words', 'txt'
    """
    if filetype == 'txt':
        s = []
        for line in open(filename, 'r'):
            s.append(line.strip().split(' '))
    else:
        s = []
        start_prev = 0.0
        for line in open(filename):
            if filetype == 'phones':
                line = line.strip().split()
                if foldphones:
                    symbol = fold(line[2])
                else:
                    symbol = line[2]
                s.append((symbol, Interval(float(line[0]), float(line[1]))))
                continue
            elif filetype == 'words':
                m = match(__wordsp, line)
            else:
                raise ValueError("filetype must be one of "
                                 "'phones', 'words', 'txt'")
            if m is None:
                continue
            end = float(m.group('end'))
            symbol = m.group('symbol') \
                .replace(';', '').replace('*', '').strip()
            if symbol == '':
                continue
            if foldphones and filetype == 'phones':
                symbol = fold(symbol)
            s.append((symbol, Interval(start_prev, end)))
            start_prev = end
    return s


def get_filesets():
    for wavfile in util.rglob(datadir, '*.wav'):
        if path.basename(wavfile).startswith('._'):
            continue
        wordsfile = path.splitext(wavfile)[0] + '.words'
        txtfile = path.splitext(wavfile)[0] + '.txt'
        phonesfile = path.join(phncorrecteddir,
                               path.splitext(path.basename(wavfile))[0]
                               + '.phn')
        # phonesfile = path.splitext(wavfile)[0] + '.phones'
        if not (path.exists(wordsfile) and
                path.exists(txtfile) and
                path.exists(phonesfile)):
            continue
        yield FileSet(wav=wavfile,
                      phones=phonesfile,
                      txt=txtfile,
                      words=wordsfile)


def fold(phone):
    try:
        return __fold[phone]
    except KeyError:
        return phone


def phongold():
    for phnfile, _, _, _ in get_filesets():
        bname = path.splitext(path.basename(phnfile))[0]
        for idx, pair in enumerate(util.split(extract_content(phnfile,
                                                              'phones'),
                                              lambda x: x[0] == '__')):
            try:
                phones, intervals = zip(*pair)
            except ValueError as e:
                print bname, pair
                raise e
            yield bname + '_{0}'.format(idx), phones, intervals

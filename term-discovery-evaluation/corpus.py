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

__phonesp = compile(r"^ *(?P<end>\d+(?:\.\d*)?|\.\d+) +\d+ +(?P<symbol>.+)$")
__wordsp = compile(r"^ *(?P<end>\d+(?:\.\d*)?|\.\d+)"
                   " +\d+ +(?P<symbol>.+?);.*$")
Interval = namedtuple('Interval', ['start', 'end'])
Interval.__repr__ = lambda x: '[{0}, {1}]'.format(x.start, x.end)
FileSet = namedtuple('FileSet', ['phones', 'words', 'txt', 'wav'])

with open('buckeye_foldings.json') as fid:
    __fold = json.load(fid)


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
                m = match(__phonesp, line)
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
        phonesfile = path.splitext(wavfile)[0] + '.phones'
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

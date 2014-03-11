#!/usr/bin/python
# -*- coding: utf-8 -*-

# ------------------------------------
# file: symbols.py
# date: Wed March 05 15:19 2014
# author:
# Maarten Versteegh
# github.com/mwv
# maartenversteegh AT gmail DOT com
#
# Licensed under GPLv3
# ------------------------------------
"""symbols:

"""


SPLITS = """<EXCLUDE-name>
__
<EXCLUDE>
<exclude-Name>
EXCLUDE
IVER
IVER-LAUGH
LAUGH
NOISE
SIL
UNKNOWN
VOCNOISE""".split('\n')

IGNORE = """{B_TRANS}
{E_TRANS}""".split('\n')

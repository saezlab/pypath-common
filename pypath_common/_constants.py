#!/usr/bin/env python

#
#  This file is part of the `pypath` python module
#
#  Copyright 2014-2023
#  EMBL, EMBL-EBI, Uniklinik RWTH Aachen, Heidelberg University
#
#  Authors: see the file `README.rst`
#  Contact: Dénes Türei (turei.denes@gmail.com)
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      https://www.gnu.org/licenses/gpl-3.0.html
#
#  Website: https://pypath.omnipathdb.org/
#
#
#  This file is part of the `pypath` python module
#

__all__ = [
    'BOOLEAN_FALSE',
    'BOOLEAN_TRUE',
    'BOOLEAN_VALUES',
    'CHAR_TYPES',
    'CURSOR_UP_ONE',
    'ERASE_LINE',
    'GLOM_ERROR',
    'LIST_LIKE',
    'NOT_ORGANISM_SPECIFIC',
    'NO_VALUE',
    'NUMERIC_TYPES',
    'SIMPLE_TYPES',
]

from typing import Mapping, Iterator, KeysView, Generator, ItemsView, ValuesView

NO_VALUE = 'PYPATH_NO_VALUE'
GLOM_ERROR = 'PYPATH_GLOM_ERROR'
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'
NOT_ORGANISM_SPECIFIC = -1
BOOLEAN_TRUE = frozenset(('1', 'yes', 'true'))
BOOLEAN_FALSE = frozenset(('0', 'no', 'false'))
BOOLEAN_VALUES = BOOLEAN_TRUE.union(BOOLEAN_FALSE)
SIMPLE_TYPES = (int, float, str, bytes, bool, type(None))
NUMERIC_TYPES = (int, float)
CHAR_TYPES = (str, bytes)
LIST_LIKE = (
    list,
    set,
    frozenset,
    tuple,
    Generator,
    ItemsView,
    Iterator,
    KeysView,
    Mapping,
    ValuesView,
)

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
#  Contains helper functions shared by different modules.
#

from __future__ import annotations

from typing import Any, Union, Literal, Hashable, Iterator, Optional
from numbers import Number
from collections.abc import Mapping, Callable, Iterable, Sequence, Collection
import os
import re
import sys
import copy
import types
import random
import hashlib
import inspect
import pathlib as pl
import operator
import textwrap
import warnings
import functools
import importlib
import itertools
import collections

import psutil
import tabulate

import numpy as np

import pypath_common.data as _data
import pypath_common._constants as const

# TODO requires cleaning, check what functions are not used and may be removed.
# Some parts can go to jsons.

__all__ = [
    'aacodes',
    'aaletters',
    'aanames',
    'add_method',
    'add_to_list',
    'add_to_set',
    'amino_acids',
    'aminoa_1_to_3_letter',
    'aminoa_3_to_1_letter',
    'at_least_in',
    'caller_module',
    'clean_dict',
    'code_to_func',
    'combine_attrs',
    'compr',
    'console',
    'decode',
    'del_empty',
    'df_memory_usage',
    'dict_collapse_keys',
    'dict_counts',
    'dict_diff',
    'dict_expand_keys',
    'dict_percent',
    'dict_set_path',
    'dict_set_percent',
    'dict_str',
    'dict_subtotals',
    'dict_sym_diff',
    'dict_union',
    'eq',
    'filtr',
    'first',
    'first_value',
    'flat_list',
    'float_or_nan',
    'format_bytes',
    'from_module',
    'get',
    'get_args',
    'identity',
    'ignore_unhashable',
    'igraph_graphics_attrs',
    'is_float',
    'is_int',
    'is_str',
    'jaccard_index',
    'join_dicts',
    'latex_table',
    'log_memory_usage',
    'match',
    'maybe_in_dict',
    'md5',
    'merge_dicts',
    'mod_keywords',
    'module_datadir',
    'module_path',
    'n_shared_elements',
    'n_shared_foreach',
    'n_shared_total',
    'n_shared_unique_foreach',
    'n_unique_elements',
    'n_unique_foreach',
    'n_unique_total',
    'negate',
    'nest',
    'none_or_len',
    'not_none',
    'paginate',
    'pmod_bel',
    'pmod_bel_to_other',
    'pmod_other_to_bel',
    'prefix',
    'print_table',
    'psite_mod_types',
    'psite_mod_types2',
    'python_memory_usage',
    'random_string',
    're_safe_groups',
    'remove_prefix',
    'remove_suffix',
    'sets_to_sorted_lists',
    'sfirst',
    'shared_elements',
    'shared_foreach',
    'shared_total',
    'shared_unique',
    'shared_unique_foreach',
    'shared_unique_total',
    'simpson_index',
    'simpson_index_counts',
    'sorensen_index',
    'suffix',
    'sum_dicts',
    'swap_dict',
    'swap_dict_simple',
    'swap_suffix',
    'table_add_row_numbers',
    'table_format',
    'table_textwrap',
    'to_float',
    'to_int',
    'to_list',
    'to_set',
    'to_tuple',
    'try_bool',
    'try_float',
    'tsv_table',
    'unique_elements',
    'unique_foreach',
    'unique_list',
    'unique_total',
    'upper0',
    'values',
    'wrap_truncate',
]


def aacodes() -> dict[str, str]:
    """
    Mapping between single letter and three letters amino acid codes.
    """

    return _data.module_data('aacodes')


def aanames() -> dict[str, str]:
    """
    Mapping between common names and single letter codes of amino acids.
    """

    return _data.module_data('aanames')


def mod_keywords() -> dict[str, list]:
    """
    Resource specific post-translational modification name patterns.
    """

    return _data.module_data('mod_keywords')


def aaletters() -> dict[str, str]:
    """
    Mapping between three letters and single letter amino acid codes.
    """
    return swap_dict(aacodes())


refloat = re.compile(r'\s*-?\s*[\s\.\d]+\s*')
reint = re.compile(r'\s*-?\s*[\s\d]+\s*')
non_digit = re.compile(r'[^\d.-]+')


def _to_number(num: Any, to: type, recursive: bool = False) -> Any:
    """
    Convert `num` to `to` if possible, return it unchanged otherwise.
    """

    if isinstance(num, to):

        return num

    elif isinstance(num, str) and globals()[f'is_{to.__name__}'](num):

        return to(num)

    elif recursive and isinstance(num, const.LIST_LIKE):

        container = type(num) if type(num) in {tuple, set} else list

        return container(_to_number(n, to, recursive) for n in num)

    else:

        try:

            return to(num)

        except TypeError:

            return num


def to_float(num: Any, recursive: bool = False) -> Any:
    """
    Convert `num` to float if possible, return it unchanged otherwise.

    Args:
        num:
            The value to convert.
        recursive:
            Convert elements of iterables recursively.
    """

    return _to_number(num, float, recursive)


def to_int(num: Any, recursive: bool = False) -> Any:
    """
    Convert `num` to integer if possible, return it unchanged otherwise.

    Args:
        num:
            The value to convert.
        recursive:
            Convert elements of iterables recursively.
    """

    return _to_number(num, int, recursive)


def is_float(num: str) -> bool:
    """
    Tells if a string can be converted to float.

    Tells if a string represents a floating point number,
    i.e. it can be converted by `float`.
    """

    return bool(refloat.match(num))


def is_int(num: str) -> bool:
    """
    Tells if a string can be converted to a number.

    Tells if a string represents an integer, i.e. it can be converted by `int`.
    """

    return bool(reint.match(num))


def float_or_nan(num: str) -> float:
    """
    Convert to float or return NaN.

    Returns:
        `num` converted from string to float if `num` represents a
        float, otherwise `numpy.nan`.
    """

    return float(num) if is_float(num) else np.nan


def try_float(num: str) -> Any:
    """
    Convert to float if possible.

    Returns `num` converted from string to float `num` represents a
    float otherwise returns the input unchanged.
    """

    try:

        return float(num)

    except ValueError:

        return num


def try_bool(val: Any) -> Any:
    """
    Convert to boolean if possible.

    Attempts to convert a value to True or False, returns the input unchanged
    upon failure.
    """

    _val = str(val).strip().lower()

    return (
        True if _val in const.BOOLEAN_TRUE else
        False if _val in const.BOOLEAN_FALSE else val
    )


def to_set(var: Any) -> set:
    """
    Convert various values to set.

    Makes sure the object `var` is a set, if it is a list converts it to set,
    otherwise it creates a single element set out of it.
    If `var` is None returns empty set.
    """

    if isinstance(var, set):

        return var

    elif var is None:

        return set()

    elif not isinstance(var, str) and hasattr(var, '__iter__'):

        return set(var)

    else:

        return {var}


def to_list(var: Any) -> list:
    """
    Convert various values to list.

    Makes sure `var` is a list otherwise creates a single element list
    out of it. If `var` is None returns empty list.
    """

    if isinstance(var, list):

        return var

    elif var is None:

        return []

    elif not is_str(var) and hasattr(var, '__iter__'):

        return list(var)

    else:

        return [var]


def to_tuple(var):
    """
    Convert various values to tuple.

    Makes sure `var` is a tuple otherwise creates a single element tuple
    out of it. If `var` is None returns empty tuple.
    """

    return var if isinstance(var, tuple) else tuple(to_list(var))


def not_none(fun: Callable) -> Callable:
    """
    Decorator implementing `fun(var) if var is not None else None`.
    """

    def wrapper(var):

        return None if var is None else fun(var)

    return wrapper


def first_value(*args: Any) -> Any:
    """
    Returns the first non-None value of the arguments.
    """

    for arg in args:

        if arg is not None:

            return arg


# From https://twitter.com/raymondh/status/944125570534621185
def unique_list(seq: Iterable) -> list:
    """
    Reduces a list to its unique elements.

    Takes any iterable and returns a list of unique elements on it. If
    the argument is a dictionary, returns a list of unique keys.
    It preserves the order of the elements.

    Args:
        seq:
            Sequence to be processed, can be any iterable type.

    Returns:
        List of unique elements in the sequence *seq*.

    Examples:
        >>> unique_list('aba')
        ['a', 'b']
        >>> unique_list([0, 1, 2, 1, 0])
        [0, 1, 2]
    """

    return list(dict.fromkeys(seq))


def flat_list(lst: Iterable[Iterable]) -> list:
    """
    Coerces the elements of a list of iterables into a single list.

    Args:
        lst:
            List to be flattened. Its elements can be also lists or any
            other iterable.

    Returns:
        Flattened list of *lst*.

    Examples:
        >>> flat_list([(0, 1), (1, 1), (2, 1)])
        [0, 1, 1, 1, 2, 1]
        >>> flat_list(['abc', 'def'])
        ['a', 'b', 'c', 'd', 'e', 'f']
    """

    return [it for sl in lst for it in sl]


def del_empty(lst: Iterable) -> list:
    """
    Remove empty entries of a list.

    It is assumed that elemenst of *lst* are iterables (e.g. [str] or
    [list]).

    Args:
        lst:
            List from which empty elements will be removed.

    Returns:
        A copy of *lst* without elements whose length was zero.

    Examples:
        >>> del_empty(['a', '', 'b', 'c'])
        ['a', 'b', 'c']
    """

    return [i for i in lst if i or isinstance(i, const.NUMERIC_TYPES)]


def re_safe_groups(
    pattern: str,
    string: str,
    method: Callable = re.search,
) -> tuple[Optional[str]]:
    """
    Extract a regex if possible.

    Missing convenience for the built-in `re` module.
    """

    match = method(pattern, string)

    return match.groups() if match else (None,)


def add_to_list(lst: list, toadd: Any) -> list:
    """
    Add elements to a list.

    Appends *toadd* to *lst*. Function differs from
    :py:func:`list.append` since is capable to handle different data
    types. This is, if *lst* is not a list, it will be converted to one.
    Similarly, if *toadd* is not a list, it will be converted and added.
    If *toadd* is or contains ``None``, these will be ommited. The
    returned list will only contain unique elements and does not
    necessarily preserve order.

    Args:
        lst:
            List or any other type (will be converted into a list). Original
            sequence to which *toadd* will be appended.
        toadd:
            Element(s) to be added to *lst*.

    Returns:
        Contains the unique element(s) from the union of *lst* and *toadd*.

    Examples:
        >>> add_to_list('ab', 'cd')
        ['ab', 'cd']
        >>> add_to_list('ab', ['cd', None, 'ab', 'ef'])
        ['ab', 'ef', 'cd']
        >>> add_to_list((0, 1, 2), 4)
        [0, 1, 2, 4]
    """

    if type(lst) is not list:

        if type(lst) in const.SIMPLE_TYPES:
            lst = [lst]

        else:
            lst = list(lst)

    if toadd is None:
        return lst

    if type(toadd) in const.SIMPLE_TYPES:
        lst.append(toadd)

    else:

        if type(toadd) is not list:
            toadd = list(toadd)

        lst.extend(toadd)

    if None in lst:
        lst.remove(None)

    return unique_list(lst)


def add_to_set(st: set, toadd: Any) -> set:
    """
    Adds elements to a set.

    Appends *toadd* to *st*. Function is capable to handle different
    input data types. This is, if *toadd* is a list, it will be
    converted to a set and added.

    Args:
        st:
            Original set to which *toadd* will be added.
        toadd:
            Element(s) to be added into *st*.

    Returns:
        Contains the element(s) from the union of *st* and *toadd*.

    Examples:
        >>> st = set([0, 1, 2])
        >>> add_to_set(st, 3)
        set([0, 1, 2, 3])
        >>> add_to_set(st, [4, 2, 5])
        set([0, 1, 2, 4, 5])
    """

    if isinstance(toadd, const.SIMPLE_TYPES):
        st.add(toadd)

    if isinstance(toadd, list):
        toadd = set(toadd)

    if isinstance(toadd, set):
        st.update(toadd)

    return st


def upper0(string: str) -> str:
    """
    Make the first letter upper case (capitalize).

    Ensures the first letter of a string is uppercase, except if the first
    word already contains uppercase letters, in order to avoid changing,
    for example, miRNA to MiRNA.
    """

    if not string:

        return string

    else:

        words = string.split(' ', maxsplit = 1)

        if words[0] and words[0].lower() == words[0]:

            words[0] = words[0][0].upper() + words[0][1:]

        return ' '.join(words)


def first(it: Iterable, default: Optional[Any] = None) -> Any:
    """
    Get the first element.

    Returns the first element of the iterable ``it`` or the value of
    ``default`` if the iterable is empty.
    """

    for i in it:

        return i

    return default


def sfirst(
    it: Union[Iterable, const.SIMPLE_TYPES],
    default: Optional[Any] = None,
) -> Any:
    """
    Get the first element, pass through if not an iterable.

    Returns ``it`` if it's a string, its first element if it's an iterable,
    or the value of ``default`` if the iterable is empty.
    """

    return it if isinstance(it, const.SIMPLE_TYPES) else first(it, default)


def swap_suffix(name: str, sep: str = '_', suffixes: Optional[Mapping] = None):
    """
    Change the suffix of a string.

    suffixes : dict
        A mapping for the swap, by default is `{'a': 'b', 'b': 'a'}`.
    """

    suffixes = suffixes or {'a': 'b', 'b': 'a'}

    name_suffix = name.rsplit(sep, maxsplit = 1)

    if len(name_suffix) == 2 and name_suffix[1] in suffixes:

        name = f'{name_suffix[0]}{sep}{suffixes[name_suffix[1]]}'

    return name


def random_string(length: int = 5) -> str:
    """
    Generates a random alphanumeric string.

    Args:
        length:
            Optional, ``5`` by default. Specifies the length of the random
            string.

    Returns:
        Random alphanumeric string of the specified length.
    """

    abc = '0123456789abcdefghijklmnopqrstuvwxyz'

    return ''.join(random.choice(abc) for i in range(length))


# XXX: Are you sure this is the way to compute Simpson's index?
# Yes this is the formula:
# https://proceedings.neurips.cc/paper/2006/file/
# a36e841c5230a79c2102036d2e259848-Paper.pdf
def simpson_index(a: Iterable[Hashable], b: Iterable[Hashable]) -> float:
    """
    Compute the Simpson's similarity index.

    Given two sets *a* and *b*, returns the Simpson index.

    Args:
        a:
            Or any iterable type (will be converted to set).
        b:
            Or any iterable type (will be converted to set).

    Returns:
        The Simpson index between *a* and *b*.
    """

    a = set(a)
    b = set(b)
    ab = a & b

    return float(len(ab)) / float(min(len(a), len(b)))


# XXX: Related to comment above, what is this exactly?
def simpson_index_counts(a: int, b: int, c: int) -> float:
    """
    Simpson index from counts.

    Args:
        a:
            Number of elements in one set.
        b:
            Number of elements in another set.
        c:
            Number of elements shared between the two sets.

    Returns:
        The Simpson index between *a* and *b*.
    """

    return c / min(a, b) if min(a, b) > 0 else 0.0


def sorensen_index(a: Iterable[Hashable], b: Iterable[Hashable]) -> float:
    """
    Compute the Sorensen index.

    Computes the Sorensen-Dice coefficient between two sets *a* and *b*.

    Args:
        a:
            Or any iterable type (will be converted to set).
        b:
            Or any iterable type (will be converted to set).

    Returns:
        The Sorensen-Dice coefficient between *a* and *b*.
    """

    a = set(a)
    b = set(b)
    ab = a & b

    return float(len(ab)) / float(len(a) + len(b))


def jaccard_index(a: Iterable[Hashable], b: Iterable[Hashable]) -> float:
    """
    Compute the Jaccard index.

    Computes the Jaccard index between two sets *a* and *b*.

    Args:
        a:
            An iterable of hashable elements.
        b:
            An iterable of hashable elements.

    Returns:
        The Jaccard index between *a* and *b*.
    """

    a = set(a)
    b = set(b)
    ab = a & b

    return float(len(ab)) / float(len(a | b))


def console(message: str):
    """
    Print a message on the terminal.

    Prints a *message* to the standard output (e.g. terminal) formatted
    to 80 characters per line plus first-level indentation.

    Args:
        message:
            The message to be printed.
    """

    message = '\n\t'.join(textwrap.wrap(message, 80))
    sys.stdout.write(('\n\t' + message).ljust(80))
    sys.stdout.write('\n')
    sys.stdout.flush()


# XXX: Not very clear to me the purpose of this function.
def get_args(loc_dict: dict, remove: Optional[Iterable[str]] = None) -> dict:
    """
    Extract the arguments from local variables.

    Given a dictionary of local variables, returns a copy of it without
    ``'self'``, ``'kwargs'`` (in the scope of a :py:obj:`class`) plus
    any other specified in the keyword argument *remove*.

    Args:
        loc_dict:
            Dictionary containing the local variables (e.g. a call to
            :py:func:`locals` in a given scope).
        remove:
            Optional, ``set([])`` by default. Can also be a list. Contains
            the keys of the elements in *loc_dict* that will be removed.

    Returns:
        A copy of *loc_dict* without ``'self'``, ``'kwargs'`` and any
        other element specified in *remove*.
    """

    remove = to_set(remove) | {'self', 'kwargs'}

    args = {k: v for k, v in loc_dict.items() if k not in remove}

    if 'kwargs' in loc_dict:
        args = dict(args.items() + loc_dict['kwargs'].items())

    return args


def clean_dict(dct: dict) -> dict:
    """
    Clean a dictionary of ``None`` values.

    Removes ``None`` values from  a dictionary *dct* and casts all other
    values to strings.

    Args:
        dct:
            Dictionary to be cleaned from ``None`` values.

    Returns:
        Copy of *dct* without ``None`` value entries and all
        other values formatted to strings.
    """

    to_del = []

    for k, v in dct.items():

        if v is None:
            to_del.append(k)

        else:
            dct[k] = str(v)

    for k in to_del:
        del dct[k]

    return dct


def md5(value: Any) -> str:
    """
    MD5 checksum of *value*.

    Args:
        value:
            Or any other type (will be converted to string). Value for which
            the MD5 sum will be computed. Must follow ASCII encoding.

    Returns
        Hash value resulting from the MD5 sum of the *value* string.
    """

    if not isinstance(value, (str, bytes)):

        value = str(value)

    if hasattr(value, 'encode'):

        value = value.encode('utf-8')

    return hashlib.md5(value).hexdigest()


def igraph_graphics_attrs() -> dict[str, list]:
    """
    Igraph graphics parameters for edges and vertices.
    """

    return _data.module_data('igraph_graphics_attrs')


def merge_dicts(d1: dict, d2: dict) -> dict:
    """
    Merges dictionaries recursively.

    If a key exists in both dictionaries, the values will be merged.

    Args:
    :arg dict d1:
        Base dictionary where *d2* will be merged.
    :arg dict d1:
        Dictionary to be merged into *d1*.

    Returns:
        Resulting dictionary from the merging.
    """

    for k2, v2 in d2.items():
        t = type(v2)

        if k2 not in d1:
            d1[k2] = v2

        elif t is dict:
            d1[k2] = merge_dicts(d1[k2], v2)

        elif t is list:
            d1[k2].extend(v2)

        elif t is set:
            d1[k2].update(v2)

    return d1


def dict_set_path(d: dict, path: Sequence) -> dict:
    """
    Create or set a path in a nested dict.

    Given a dictionary of dictionaries *d* looks up the keys according
    to *path*, creates new subdicts and keys if those do not exist yet,
    and sets/merges the leaf element according to simple heuristic.

    Args:
        d:
            Dictionary of dictionaries for which the path is to be set.
        path:
            Or tuple, contains the path of keys being the first element a
            key of *d* (if doesn't exist will be created), and the
            subsequent of the inner dictionaries. The last element is the
            value that will be set/merged on the specified path.

    Returns:
        A copy of *d* including the specified *path*.

    Example:
        >>> dict_set_path(dict(), ['a', 'b', 1])
        {'a': {'b': 1}}
    """

    val = path[-1]
    key = path[-2]
    subd = d

    for k in path[:-2]:

        if type(subd) is dict:

            if k in subd:
                subd = subd[k]

            else:
                subd[k] = {}
                subd = subd[k]

        else:
            return d

    if key not in subd:
        subd[key] = val

    elif type(val) is dict and type(subd[key]) is dict:
        subd[key].update(val)

    elif type(subd[key]) is list:

        if type(val) is list:
            subd[key].extend(val)

        else:
            subd[key].append(val)

    elif type(subd[key]) is set:

        if type(val) is set:
            subd[key].update(val)

        else:
            subd[key].add(val)

    return d


def dict_diff(d1: dict, d2: dict) -> tuple[dict, dict]:
    """
    Compare two dictionaries.

    Compares two given dictionaries *d1* and *d2* whose values are sets
    or dictionaries (in such case the function is called recursively).
    **NOTE:** The comparison is only performed on the values of the
    keys that are common in *d1* and *d2* (see example below).

    Args:
        d1:
            First dictionary of the comparison.
        d2:
            Second dictionary of the comparison.

    Returns:
        Unique elements of *d1* when compared to *d2*.
        Unique elements of *d2* when compared to *d1*.

    Examples:
        >>> d1 = {'a': {1}, 'b': {2}, 'c': {3}} # 'c' is unique to d1
        >>> d2 = {'a': {1}, 'b': {3}}
        >>> dict_diff(d1, d2)
        ({'a': set([]), 'b': set([2])}, {'a': set([]), 'b': set([3])})
    """

    ldiff = {}
    rdiff = {}
    keys = set(d1.keys()) & set(d2.keys())

    for k in keys:

        if type(d1[k]) is dict and type(d2[k]) is dict:
            ldiff[k], rdiff[k] = dict_diff(d1[k], d2[k])

        elif type(d1[k]) is set and type(d2[k]) is set:
            ldiff[k], rdiff[k] = (d1[k] - d2[k], d2[k] - d1[k])

    return ldiff, rdiff


def dict_sym_diff(d1: dict, d2: dict) -> dict:  # XXX: Not used
    """
    Symmetric difference of dictionaries.
    """

    diff = {}
    keys = set(d1.keys()) & set(d2.keys())

    for k in keys:

        if type(d1[k]) is dict and type(d2[k]) is dict:
            diff[k] = dict_sym_diff(d1[k], d2[k])

        elif type(d1[k]) is set and type(d2[k]) is set:
            diff[k] = d1[k] ^ d2[k]

    return diff


def swap_dict(d: dict, force_sets: bool = False) -> dict:
    """
    Swaps a dictionary.

    Interchanges the keys and values of a dictionary. If the values are
    lists (or any iterable type) and/or not unique, each unique element
    will be a key and values sets of the original keys of *d* (see
    example below).

    Args:
        d:
            Original dictionary to be swapped.
        force_sets:
            The values of the swapped dict should be sets
            even if all of them have only one item.

    Returns:
        The swapped dictionary.

    Examples:
        >>> d = {'a': 1, 'b': 2}
        >>> swap_dict(d)
        {1: 'a', 2: 'b'}
        >>> d = {'a': 1, 'b': 1, 'c': 2}
        >>> swap_dict(d)
        {1: set(['a', 'b']), 2: set(['c'])}
        d = {'a': [1, 2, 3], 'b': [2, 3]}
        >>> swap_dict(d)
        {1: set(['a']), 2: set(['a', 'b']), 3: set(['a', 'b'])}
    """

    _d = {}

    for key, vals in d.items():

        vals = [vals] if type(vals) in const.SIMPLE_TYPES else vals

        for val in vals:

            _d.setdefault(val, set()).add(key)

    if not force_sets and all(len(v) <= 1 for v in _d.values()):

        _d = {k: list(v)[0] for k, v in _d.items() if len(v)}

    return _d


def swap_dict_simple(d: dict[Hashable, Hashable]) -> dict:
    """
    Swaps a dictionary.

    Interchanges the keys and values of a dictionary. Assumes the values
    are unique and hashable, otherwise overwrites duplicates or raises
    error.

    Args:
        d:
            Original dictionary to be swapped.

    Returns:
        The swapped dictionary.
    """

    return {v: k for k, v in d.items()}


# XXX: Not sure what this joins exactly... I tried:
#      >>> a = {'a': [1], 'b': [2]}
#      >>> b = {'a': [2], 'b': [4]}
#      >>> join_dicts(a, b)
#      and got an empty dictionary (?)


def join_dicts(d1, d2, _from = 'keys', to = 'values'):  # TODO
    """
    Joins a pair of dictionaries.

    Args:
    :arg dict d1:
        Dictionary to be merged with *d2*
    :arg dict d2:
        Dictionary to be merged with *d1*
    :arg str _from:
        Optional, ``'keys'`` by default.
    :arg str to:
        Optional, ``'values'`` by default.

    Returns:
        (*dict*) -- .
    """

    result = {}

    if to == 'keys':
        d2 = swap_dict(d2)

    for key1, val1 in d1.items():
        sources = (
            [key1] if _from == 'keys' else
            [val1] if type(val1) in const.SIMPLE_TYPES else val1
        )
        meds = (
            [key1] if _from == 'values' else
            [val1] if type(val1) in const.SIMPLE_TYPES else val1
        )
        targets = set()

        for med in meds:

            if med in d2:

                if type(targets) is list:
                    targets.append(d2[med])

                elif type(d2[med]) in const.SIMPLE_TYPES:
                    targets.add(d2[med])

                elif type(d2[med]) is list:
                    targets.update(set(d2[med]))

                elif type(d2[med]) is set:
                    targets.update(d2[med])

                elif d2[med].__hash__ is not None:
                    targets.add(d2[med])

                else:
                    targets = list(targets)
                    targets.append(d2[med])

        for source in sources:

            if type(targets) is list:

                if source not in result:
                    result[source] = []

                result[source].extend(targets)

            elif type(targets) is set:

                if source not in result:
                    result[source] = set()

                result[source].update(targets)

    if all(len(x) <= 1 for x in result.values()):
        result = {k: list(v)[0] for k, v in result.items() if len(v)}

    return result


def psite_mod_types() -> list[tuple[str, str]]:
    """
    PhosphoSite PTM type codes.
    """  # noqa: D403

    return _data.module_data('psite_mod_types')


def psite_mod_types2() -> list[tuple[str, str]]:
    """
    PhosphoSite PTM type codes, version 2.
    """  # noqa: D403

    return _data.module_data('psite_mod_types2')


def pmod_bel() -> tuple[tuple[str, tuple[str]]]:
    """
    BEL (Biological Expression Language) PTM type codes and keywords.
    """

    return _data.module_data('pmod_bel')


def pmod_bel_to_other() -> dict[str, tuple[str]]:
    """
    BEL (Biological Expression Language) PTM type codes and keywords.
    """

    return dict(pmod_bel())


def pmod_other_to_bel() -> dict[str, str]:
    """
    BEL (Biological Expression Language) PTM type codes and keywords.
    """

    return {
        other_name: bel_name
        for bel_name, other_names in pmod_bel() for other_name in other_names
    }


def amino_acids() -> tuple[tuple[str]]:
    """
    Amino acid names, three letters and single letter codes.
    """

    return _data.module_data('amino_acids')


def aminoa_3_to_1_letter() -> dict[str, str]:
    """
    Mapping from amino acid 3 letters to single letter codes.
    """

    return {code3: code1 for name, code3, code1 in amino_acids()}


def aminoa_1_to_3_letter() -> dict[str, str]:
    """
    Mapping from amino acid single letter to 3 letters codes.
    """

    return {code1: code3 for name, code3, code1 in amino_acids()}


def paginate(lst: Collection, size: int = 10) -> list[list]:
    """
    Paginate a list.

    Yields sections of length ``size`` from list ``lst``.
    The last section might be shorter than ``size``.
    Following https://stackoverflow.com/a/3744502/854988.
    """

    for i in range((len(lst) // size) + 1):

        yield lst[size * i:size * (i + 1)]  # noqa: E203


def shared_unique(
        by_group: dict[Hashable, set],
        group: str,
        op: Literal['shared', 'unique'] = 'shared',
) -> set:
    """
    Collect elements unique or shared between one set versus a dict of sets.

    For a *dict* of *set*s ``by_group`` and a particular key ``group``
    returns a *set* of all elements in the *set* belonging to the
    key ``group`` which either does or does not occure in any of the sets
    assigned to the other keys, depending on the operator ``op``.
    This method can be used among other things to find the shared and
    unique entities across resources.

    Args:
        by_group:
            The elements grouped into sets.
        group:
            Key for the group of interest.
        op:
            Either `shared` or `unique`.

    Returns:
        A set of elements in the group of interest that are either unique
        to this group, or shared with at least one other group.
    """

    if group not in by_group:

        warnings.warn(
            f'Group `{group}` missing from the dict of groups!',
            stacklevel = 2,
        )

    _op = operator.sub if op == 'unique' else operator.and_

    return _op(
        by_group[group] if group in by_group else set(),
        set.union(
            set(),
            *(
                elements for label, elements in by_group.items()
                if label != group
            ),
        ),
    )


def shared_elements(by_group: dict[Hashable, set], group: str) -> set:
    """
    Collect shared elements between one set and other sets.

    For a *dict* of *set*s ``by_group`` and a particular key ``group``
    returns a *set* of all elements in the *set* belonging to the
    key ``group`` which occure in any of the sets assigned to the other keys.
    This method can be used among other things to find the shared entities
    across resources.

    Args:
        by_group:
            The elements grouped into sets.
        group:
            Key for the group of interest.

    Returns:
        A set of elements in the group of interest that are shared between
        this group and at least one other group.
    """

    return shared_unique(
        by_group = by_group,
        group = group,
        op = 'shared',
    )


def unique_elements(by_group, group):
    """
    Collect elements of one set that do not occur in other sets.

    For a *dict* of *set*s ``by_group`` and a particular key ``group``
    returns a *set* of all elements in the *set* belonging to the
    key ``group`` which don't occure in any of the sets assigned to the
    other keys. This method can be used among other things to find the
    unique entities across resources.

    Args:
        by_group:
            The elements grouped into sets.
        group:
            Key for the group of interest.

    Returns:
        A set of elements in the group of interest that are unique for
        this group (can not be found in any other group).
    """

    return shared_unique(
        by_group = by_group,
        group = group,
        op = 'unique',
    )


def n_shared_elements(by_group: dict[Hashable, set], group: str) -> int:
    """
    Count shared elements between one set and other sets.

    For a *dict* of *set*s ``by_group`` and a particular key ``group``
    returns the number of all elements in the *set* belonging to the
    key ``group`` which occure in any of the other sets.
    This method can be used among other things to count the shared entities
    across resources.

    Args:
        by_group:
            The elements grouped into sets.
        group:
            Key for the group of interest.

    Returns:
        The number of elements in the group of interest that are shared
        between this group and at least one other group.
    """

    return len(shared_elements(by_group = by_group, group = group))


def n_unique_elements(by_group: dict[Hashable, set], group: str) -> int:
    """
    Count elements of one set that do not occur in other sets.

    For a *dict* of *set*s ``by_group`` and a particular key ``group``
    returns the number of all elements in the *set* belonging to the
    key ``group`` which don't occure in any of the other sets.
    This method can be used among other things to count the unique entities
    across resources.

    Args:
        by_group:
            The elements grouped into sets.
        group:
            Key for the group of interest.

    Returns:
        The count of elements in the group of interest that are unique for
        this group (can not be found in any other group).
    """

    return len(unique_elements(by_group = by_group, group = group))


def shared_unique_foreach(
        by_group: dict[Hashable, set],
        op: Literal['shared', 'unique'] = 'shared',
        counts: bool = False,
) -> dict[Hashable, Union[set, int]]:
    """
    For each set collect its shared or unique elements.

    For a *dict* of *set*s ``by_group`` returns a *dict* of *set*s with
    either shared or unique elements across all *set*s, depending on
    the operation ``op``.

    Args:
        by_group:
            The elements grouped into sets.
        op:
            Either `shared` or `unique`.

    Returns:
        A dict with shared or unique elements for each set, respective to
        all other sets, or the count of those elements if `counts` is `True`.
    """

    method = len if counts else lambda x: x

    return {
        label: method(
            shared_unique(
                by_group = by_group,
                group = label,
                op = op,
            ),
        )
        for label in by_group.keys()
    }


def n_shared_unique_foreach(
        by_group: dict[Hashable, set],
        op: Literal['shared', 'unique'] = 'shared',
) -> dict[Hashable, int]:
    """
    For each set count its shared or unique elements.

    For a *dict* of *set*s ``by_group`` returns a *dict* of numbers with
    the counts of either the shared or unique elements across all *set*s,
    depending on the operation ``op``.

    Args:
        by_group:
            The elements grouped into sets.
        op:
            Either `shared` or `unique`.

    Returns:
        A dict with the counts of shared or unique elements for each set,
        respective to all other sets.
    """

    return shared_unique_foreach(
        by_group = by_group,
        op = 'shared',
        counts = True,
    )


def shared_foreach(by_group: dict[Hashable, set]) -> dict[Hashable, set]:
    """
    For each set collect its shared elements.

    Args:
        by_group:
            The elements grouped into sets.

    Returns:
        A dict with the shared elements for each group. Shared means
        elements that can be found in more than one group.
    """

    return shared_unique_foreach(by_group = by_group, op = 'shared')


def unique_foreach(by_group: dict[Hashable, set]) -> dict[Hashable, set]:
    """
    For each set collect its unique elements.

    Args:
        by_group:
            The elements grouped into sets.

    Returns:
        A dict with the shared elements for each group. Unique means
        elements that can be found only in one group.
    """

    return shared_unique_foreach(by_group = by_group, op = 'unique')


def n_shared_foreach(by_group: dict[Hashable, set]) -> dict[Hashable, int]:
    """
    For each set count its shared elements.

    Args:
        by_group:
            The elements grouped into sets.

    Returns:
        A dict with the counts of shared elements for each group. Shared means
        elements that can be found in more than one group.
    """

    return n_shared_unique_foreach(by_group = by_group, op = 'shared')


def n_unique_foreach(by_group: dict[Hashable, set]) -> dict[Hashable, int]:
    """
    For each set count its unique elements.

    Args:
        by_group:
            The elements grouped into sets.

    Returns:
        A dict with the counts of shared elements for each group. Unique means
        elements that can be found only in one group.
    """

    return n_shared_unique_foreach(by_group = by_group, op = 'unique')


def dict_union(dict_of_sets: dict[Hashable, set]) -> set:
    """
    Union over a dict of sets.

    For a *dict* of *set*s returns the union of the values.
    """

    return set.union(*dict_of_sets.values()) if dict_of_sets else set()


def dict_counts(dict_of_sets: dict[Hashable, set]) -> dict[Hashable, int]:
    """
    Dict of counts from a dict of sets.

    For a *dict* of *set*s or other values with ``__len__`` returns a
    *dict* of numbers with the length of each value in the original *dict*.

    This function is recursively works on dicts of dicts.
    """

    return {
        key: (dict_counts(val) if isinstance(val, dict) else len(val))
        for key, val in dict_of_sets.items()
    }


def dict_expand_keys(dct: dict, depth: int = 1, front: bool = True) -> dict:
    """
    From a *dict* with *tuple* keys builds a dict of dicts.

    Args:
        dct:
            A *dict* with tuple keys (if keys are not tuples ``dct`` will be
            returned unchanged).
        depth:
            Expand the keys up to this depth. If 0 *dct* will be returned
            unchanged, if 1 dict of dicts, if 2 dict of dict of dicts will be
            returned, and so on.
        front:
            If ``True`` the tuple keys will be chopped from the front,
            otherwise from their ends.
    """

    if depth == 0:

        return dct

    new = {}

    for key, val in dct.items():

        if not isinstance(key, tuple):

            new[key] = val

        elif len(key) == 1:

            new[key[0]] = val

        else:

            outer_key = key[0] if front else key[:-1]
            inner_key = key[1:] if front else key[-1]

            if len(inner_key) == 1:

                inner_key = inner_key[0]

            sub_dct = new.setdefault(outer_key, {})
            sub_dct[inner_key] = val

    if depth > 1:

        new = (
            {
                key: dict_expand_keys(sub_dct, depth = depth - 1)
                for key, sub_dct in new.items()
            }
                if front else
            dict_expand_keys(new, depth = depth - 1, front = False)
        )

    return new


def dict_collapse_keys(
    dct: dict,
    depth: int = 1,
    front: bool = True,
    expand_tuple_keys: bool = True,
) -> dict:
    """
    From a dict of dicts builds a dict with tuple keys.

    Args:
        dct:
            A dict of dicts (if values are not dicts it will be returned
            unchanged).
        depth:
            Collapse the keys up to this depth. If 0 *dct* will be returned
            unchanged, if 1 tuple keys will have 2 elements, if 2 then
            2 elements, and so on.
        front:
            If ``True`` the tuple keys will be collapsed first from the
            outermost dict going towards the innermost one until depth allows.
            Otherwise the method will start from the innermost ones.
        expand_tuple_keys:
            If ``True`` the tuple keys of inner dicts will be concatenated
            with the outer key tuples. If ``False`` the inner tuple keys
            will be added as an element of the tuple key i.e. tuple in tuple.
    """

    if not front:

        # this is difficult to implement because we have no idea about
        # the depth; this version ensures an even key length for the
        # tuple keys; another alterntive would be to iterate recursively
        # over the dictionary tree
        dct = dict_collapse_keys(dct, depth = 9999999)
        maxdepth = max(
            len(k for k in dct.keys() if isinstance(k, tuple)),
            default = 0,
        )
        return dict_expand_keys(dct, depth = maxdepth - depth, front = True)

    if not any(isinstance(val, dict) for val in dct.values()):

        return dct

    new = {}

    for key, val in dct.items():

        key = key if isinstance(key, tuple) else (key,)

        if isinstance(val, dict):

            for key1, val1 in val.items():

                _key = key + (
                    key1 if (isinstance(key1, tuple) and expand_tuple_keys) else
                    (key1,)
                )
                new[_key] = val1

        else:

            new[key] = val

    if depth > 1:

        new = dict_collapse_keys(new, depth = depth - 1)

    return new


def shared_unique_total(
    by_group: dict[Hashable, set],
    op: Literal['unique', 'shared'] = 'shared',
) -> set:
    """
    Collect shared or unique elements across sets.

    Args:
        by_group:
            Elements grouped into sets.
        op:
            Either `shared` or `unique`.

    Returns:
        The shared or unique elements collected into one set.
    """

    counts = collections.Counter(itertools.chain(*by_group.values()))
    _op = operator.eq if op == 'unique' else operator.gt

    return {key for key, val in counts.items() if _op(val, 1)}


def shared_total(by_group: dict[Hashable, set]) -> set:
    """
    Collect shared elements across sets.

    Args:
        by_group:
            Elements grouped into sets.

    Returns:
        The shared elements collected into one set.
    """

    return shared_unique_total(by_group = by_group, op = 'shared')


def unique_total(by_group: dict[Hashable, set]) -> set:
    """
    Collect unique elements across sets.

    Args:
        by_group:
            Elements grouped into sets.

    Returns:
        The unique elements collected into one set.
    """

    return shared_unique_total(by_group = by_group, op = 'unique')


def n_shared_total(by_group: dict[Hashable, set]) -> int:
    """
    Count shared elements across sets.

    Args:
        by_group:
            Elements grouped into sets.

    Returns:
        The number of shared elements across all sets.
    """

    return len(shared_total(by_group))


def n_unique_total(by_group: dict[Hashable, set]) -> int:
    """
    Count unique elements across sets.

    Args:
        by_group:
            Elements grouped into sets.

    Returns:
        The number of unique elements across all sets.
    """

    return len(unique_total(by_group))


def dict_subtotals(
    dct: dict[Hashable, dict[Hashable, Collection]],
) -> dict[Hashable, set]:
    """
    Unions by inner keys across a dict of dicts.

    For a dict of dicts of sets returns a dict with keys of the outer dict
    and values the union of the sets in each of the inner dicts.
    """

    return {key: dict_union(sub_dct) for key, sub_dct in dct.items()}


def dict_percent(
    dict_of_counts: dict[Hashable, Number],
    total: Number,
) -> dict[Hashable, Number]:
    """
    For a *dict* of counts and a total count creates a *dict* of percentages.
    """

    return {
        key: (val / total if total != 0 else 0) * 100
        for key, val in dict_of_counts.items()
    }


def dict_set_percent(
    dict_of_sets: dict[Hashable, Collection],
) -> dict[Hashable, Number]:
    """
    Percents of overlaps for a dict of sets.
    """

    total = len(dict_union(dict_of_sets))
    counts = dict_counts(dict_of_sets)

    return dict_percent(counts, total)


def df_memory_usage(df, deep: bool = True) -> str:
    """
    Memory usage of a pandas data frame.

    Returns the memory usage of a ``pandas.DataFrame`` as a string.
    Modified from ``pandas.DataFrame.info``.

    Args:
        df:
            A pandas data frame.
        deep:
            Passed to `DataFrame.memory_usage`.

    Return:
        A string reporting memory usage (to be included in log messages).
    """

    dtypes = {str(dt) for dt in df.dtypes}

    size_qualifier = (
        '+' if
        ('object' in dtypes or df.index._is_memory_usage_qualified()) else ''
    )

    mem_usage = df.memory_usage(index = True, deep = deep).sum()

    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:

        if mem_usage < 1024.0:

            return f'{mem_usage:3.1f}{size_qualifier} {unit}'

        mem_usage /= 1024.0

    return format_bytes(mem_usage, size_qualifier)


def python_memory_usage() -> float:
    """
    Returns the memory usage of the current process in bytes.
    """

    return psutil.Process(os.getpid()).memory_info().vms


def format_bytes(bytes: float, qualifier: str = '') -> str:
    """
    Pretty printed bytes with unit.
    """

    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:

        if bytes < 1024.0:

            return f'{bytes:3.1f}{qualifier} {unit}'

        bytes /= 1024.0

    return f'{bytes:3.1f}{qualifier} PB'


def log_memory_usage():
    """
    Logs the memory usage of the current process.
    """

    import pypath
    pypath.session.log.msg(
        f'Python memory use: {format_bytes(python_memory_usage())}',
    )


def sum_dicts(*args: Iterable[dict]) -> dict[Hashable, float]:
    """
    Sum of dict values.

    For dicts of numbers returns a dict with the sum of the numbers from
    all dicts for all keys.

    Args:
        args:
            One or more dicts.

    Returns:
        A dict with a sum for each key across all dicts.
    """

    args = [collections.defaultdict(int, d) for d in args]

    return {
        key: sum(d[key] for d in args)
        for key in set(itertools.chain(*(d.keys() for d in args)))
    }


def combine_attrs(attrs: list[Any], num_method: Callable = max) -> Any:
    """
    Combine attributes recursively.

    Combines multiple attributes into one. This method attempts
    to find out which is the best way to combine attributes.

        * If there is only one value or one of them is None, then
          returns the one available.
        * Lists: concatenates unique values of lists.
        * Numbers: returns the greater by default or calls
          *num_method* if given.
        * Sets: returns the union.
        * Dictionaries: calls :py:func:`pypath_common.misc.merge_dicts`.
        * Direction: calls their special
          :py:meth:`pypath.main.Direction.merge` method.

    Works on more than 2 attributes recursively.

    Args:
        attrs:
            List of one or more attribute values.
        num_method:
            Optional, ``max`` by default. Method to merge numeric attributes.

    Returns:
        The values combined.
    """
    def list_or_set(one, two):

        if (
            isinstance(one, list) and
            isinstance(two, set)
        ) or (
            isinstance(two, list) and
            isinstance(one, set)
        ):

            try:
                return set(one), set(two)

            except TypeError:
                return list(one), list(two)

        else:
            return one, two

    # recursion:
    if len(attrs) > 2:
        attrs = [attrs[0], combine_attrs(attrs[1:], num_method = num_method)]

    # quick and simple cases:
    if len(attrs) == 0:
        return None

    if len(attrs) == 1:
        return attrs[0]

    if attrs[0] == attrs[1]:
        return attrs[0]

    if attrs[0] is None:
        return attrs[1]

    if attrs[1] is None:
        return attrs[0]

    # merge numeric values
    if isinstance(
            attrs[0],
            const.NUMERIC_TYPES,
    ) and isinstance(attrs[1], const.NUMERIC_TYPES):

        return num_method(attrs)

    attrs = list(attrs)

    # in case one is list other is set
    attrs[0], attrs[1] = list_or_set(attrs[0], attrs[1])

    # merge lists:
    if isinstance(attrs[0], list) and isinstance(attrs[1], list):

        try:
            # lists of hashable elements only:
            return list(set(itertools.chain(attrs[0], attrs[1])))

        except TypeError:
            # if contain non-hashable elements:
            return list(itertools.chain(attrs[0], attrs[1]))

    # merge sets:
    if isinstance(attrs[0], set):
        return add_to_set(attrs[0], attrs[1])

    if isinstance(attrs[1], set):
        return add_to_set(attrs[1], attrs[0])

    # merge dicts:
    if isinstance(attrs[0], dict) and isinstance(attrs[1], dict):
        return merge_dicts(attrs[0], attrs[1])

    # 2 different strings: return a set with both of them
    if is_str(attrs[0]) and is_str(attrs[1]):

        if len(attrs[0]) == 0:
            return attrs[1]

        if len(attrs[1]) == 0:
            return attrs[0]

        return {attrs[0], attrs[1]}

    # one attr is list, the other is simple value:
    if isinstance(attrs[0], list) and type(attrs[1]) in const.SIMPLE_TYPES:

        if attrs[1] in const.NUMERIC_TYPES or len(attrs[1]) > 0:
            return add_to_list(attrs[0], attrs[1])

        else:
            return attrs[0]

    if isinstance(attrs[1], list) and type(attrs[0]) in const.SIMPLE_TYPES:

        if attrs[0] in const.NUMERIC_TYPES or len(attrs[0]) > 0:
            return add_to_list(attrs[1], attrs[0])

        else:
            return attrs[1]

    # in case the objects have `__add__()` method:
    if hasattr(attrs[0], '__add__'):

        return attrs[0] + attrs[1]


def add_method(cls, method_name, method, signature = None, doc = None):
    """
    From a function create a bound method for a class.
    """

    method.__name__ = method_name

    if signature and hasattr(inspect, 'Signature'):  # Py2

        if not isinstance(signature, inspect.Signature):

            signature = inspect.Signature(
                [
                    inspect.Parameter(
                        name = param[0],
                        kind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        default = (
                            param[1] if len(param) > 1 else
                            inspect.Parameter.empty
                        ),
                    ) for param in signature
                ],
            )

        method.__signature__ = signature

    if doc:

        method.__doc__ = doc

    setattr(cls, method_name, method)


def caller_module(with_submodules: bool = False) -> str:
    """
    Name of the module indirectly calling this function.

    To find the module of interest, the stack will be traversed from bottom to
    top until a foreign module is encountered.

    Args:
        with_submodules:
            Include submodules, or return only the name of the top level
            module.

    Returns:
        The name of the module calling this function.
    """

    forbidden = {'importlib', 'console', '__main__', 'code', 'IPython'}

    mod_top = lambda mod: mod.split('.')[0]
    mod_of_fi = lambda fi: mod_top(fi.frame.f_globals['__name__'])

    stack = inspect.stack()
    this_module = mod_top(mod_of_fi(stack[0]))

    for fi in stack:

        mod_full = mod_of_fi(fi)
        mod = mod_top(mod_full)

        if mod != this_module:

            if mod in forbidden:

                break

            else:

                return mod_full if with_submodules else mod

    return this_module


def module_path(module: str, directory: bool = True) -> pl.Path | None:
    """
    For a module name returns its absolute path.

    Args:
        module:
            Name of a module.
        directory:
            Return the directory, without the file name.

    Returns:
        Path to the module file or the directory containing the module.
    """

    if spec := importlib.util.find_spec(module):

        path = pl.Path(spec.origin)

        if directory:

            path = path.parent

        return path


def module_datadir(module: str) -> pl.Path | None:
    """
    For a module name returns its data directory.

    Args:
        module:
            Name of a module.

    Returns:
        Path to the `data` or `_data` directory under the queried module, if
        such directory exist. If both exist, the path to `data` will be
        returned.
    """

    if path := module_path(module, directory = True):

        for data in ('data', '_data'):

            if (datadir := path / data).exists():

                return datadir


def at_least_in(n: int = 2) -> Callable:
    """
    An operator of "element occurs at least in N collections".

    Returns a method which is similar to the `intersection` operator on sets
    but requires the elements to present at least in ``n`` of the sets
    instead of in all of them. If ``n = 1`` it is equivalent with ``union``,
    if ``n`` is the same as the number of the sets it is equivalent with
    ``intersection``. The returned method accepts an arbitrary number of
    sets as non-keyword arguments.

    Args:
        n:
            Number of collections the element have to be found in order to
            return True.

    Returns:
        A callable that you can use as an operator to check for the desired
        number of incidence of elements.
    """
    def _at_least_in(*args):

        if len(args) < n:

            return set()

        counter = collections.Counter(itertools.chain(*args))

        return {key for key, count in counter.items() if count >= n}

    return _at_least_in


def eq(
    one: Union[Hashable, Collection[Hashable]],
    other: Union[Hashable, Collection[Hashable]],
) -> bool:
    """
    Equality between simple types and sets.

    Equality between ``one`` and ``other``. If any of them is type of `set`,
    returns True if it contains the other. If both of them are `set`,
    returns True if they share any element. Lists, tuples and similar objects
    will be converted to `set`.
    """

    one = one if isinstance(one, const.SIMPLE_TYPES) else to_set(one)
    other = other if isinstance(other, const.SIMPLE_TYPES) else to_set(other)

    if isinstance(one, set):

        if isinstance(other, set):

            return bool(one & other)

        else:

            return other in one

    elif isinstance(other, set):

        return one in other

    else:

        return one == other


def dict_str(dct: dict) -> str:
    """
    String representation of a dict.
    """

    if not isinstance(dct, dict):

        return str(dct)

    return ', '.join(f'{str(key)} = {str(val)}' for key, val in dct.items())


def none_or_len(value: Any) -> Optional[int]:
    """
    Length if possible.
    """

    return None if not hasattr(value, '__len__') else len(value)


def sets_to_sorted_lists(obj: Any) -> Any:
    """
    Sort if possible.
    """

    if isinstance(obj, dict):

        return {k: sets_to_sorted_lists(v) for k, v in obj.items()}

    elif isinstance(obj, const.LIST_LIKE):

        return sorted(obj)

    else:

        return obj


def is_str(obj: Any) -> bool:
    """
    Checks if ``obj`` is a string.
    """

    return isinstance(obj, const.CHAR_TYPES)


def wrap_truncate(
    text: Union[str, Collection],
    width: Optional[int] = None,
    maxlen: Optional[int] = None,
) -> str:
    """
    Wrap and truncate a paragraph.
    """

    if isinstance(text, const.LIST_LIKE):

        text = ', '.join(text)

    if not is_str(text):

        text = str(text)

    if maxlen:

        text = textwrap.shorten(text, width = maxlen)

    if width:

        text = textwrap.wrap(text, width = width)

    return os.linesep.join(text) if isinstance(text, const.LIST_LIKE) else text


def table_add_row_numbers(
    tbl: collections.OrderedDict, **kwargs
) -> collections.OrderedDict:
    """
    Add a column to a table with row numbers.
    """

    nrows = len(next(tbl.values().__iter__())) if len(tbl) else 0

    return collections.OrderedDict(
        itertools.chain(
            (('No.', list(range(1, nrows + 1))),),
            tbl.items(),
        ),
    )


def table_textwrap(
    tbl: collections.OrderedDict,
    width: Optional[int] = None,
    maxlen: Optional[int] = None,
) -> collections.OrderedDict:
    """
    Wraps and truncates the text content of cells in a table.

    The table is an ``OrderedDict`` with column titles as keys and column
    contents as lists.
    """
    def get_width(i):

        return (
            width[i]
                if (  # noqa: E131
                    isinstance(width, const.LIST_LIKE) or
                    (isinstance(width, dict) and i in width)
                ) else  # noqa: E123
            width['default']
                # noqa: E131
                if (isinstance(width, dict) and 'default' in width) else
            width
        )

    return collections.OrderedDict(
        (
            wrap_truncate(title, width = get_width(i), maxlen = maxlen),
            [
                wrap_truncate(cell, width = width, maxlen = maxlen)
                for cell in column
            ],
        )
        for i, (title, column) in enumerate(tbl.items())
    )


def table_format(
    tbl: collections.OrderedDict,
    width: Optional[int] = None,
    maxlen: Optional[int] = None,
    tablefmt: str = 'fancy_grid',
    wrap: bool = True,
    lineno: bool = True,
    **kwargs,
) -> str:
    """
    Format a table for terminal.
    """

    TABULATE_DEFAULTS = {
        'numalign': 'right',
    }

    if wrap:

        tbl = table_textwrap(tbl, width = width, maxlen = maxlen)

    if lineno:

        tbl = table_add_row_numbers(tbl)

    tabulate_param = copy.deepcopy(TABULATE_DEFAULTS)
    tabulate_param.update(kwargs)

    return tabulate.tabulate(
        zip(*tbl.values()), tbl.keys(), tablefmt = tablefmt, **tabulate_param
    )


def print_table(
    tbl: collections.OrderedDict,
    width: Optional[int] = None,
    maxlen: Optional[int] = None,
    tablefmt: str = 'fancy_grid',
    wrap: bool = True,
    lineno: bool = True,
    **kwargs,
):
    """
    Print a table to the terminal.
    """

    sys.stdout.write(
        table_format(
            tbl,
            width = width,
            maxlen = maxlen,
            tablefmt = tablefmt,
            wrap = wrap,
            lineno = lineno,
            **kwargs,
        ),
    )
    sys.stdout.write(os.linesep)
    sys.stdout.flush()


def tsv_table(
    tbl: collections.OrderedDict,
    path: Optional[str] = None,
    maxlen: Optional[int] = None,
    **kwargs,
) -> Optional[str]:
    """
    Create a tab separated table.

    From a table represented by an OrderedDict with column titles as keys
    and column contents as lists generates a tab separated string.
    If ``path`` provided writes out the tsv into a file, otherwise returns
    the string.
    """

    tbl = table_textwrap(tbl, width = None, maxlen = maxlen)
    tsv = []
    tsv.append('\t'.join(tbl.keys()))
    tsv.extend(['\t'.join(map(str, row)) for row in zip(*tbl.values())])
    tsv = os.linesep.join(tsv)

    if path:

        with open(path, 'w') as fp:

            fp.write(tsv)

    else:

        return tsv


def latex_table(
    tbl: collections.OrderedDict,
    colformat: Optional[str] = None,
    maxlen: Optional[int] = None,
    lineno: bool = True,
    path: Optional[str] = None,
    doc_template: bool = True,
    booktabs: bool = True,
    latex_compile: bool = False,
    latex_executable: str = 'xelatex',
    latex_engine: str = 'xelatex',
    **kwargs,
) -> Optional[str]:
    """
    Create a LaTeX table.

    From a table represented by an OrderedDict with column titles as keys
    and column contents as lists generates LaTeX tabular.
    If ``path`` provided writes out the table into a file,
    if ``latex_compile`` is True compiles the document, otherwise returns
    it as a string.
    """

    maxlen = maxlen or 999999

    _xelatex_header = [
        r'\usepackage[no-math]{fontspec}',
        r'\usepackage{xunicode}',
        r'\usepackage{polyglossia}',
        r'\setdefaultlanguage{english}',
        r'\usepackage{xltxtra}',
    ]

    _pdflatex_header = [
        r'\usepackage[utf8]{inputenc}'
        r'\usepackage[T1]{fontenc}'
        r'\usepackage[english]{babel}',
    ]

    _doc_template_default = [
        r'\documentclass[9pt, a4paper, landscape]{article}',
    ]
    _doc_template_default.extend(
        _xelatex_header if latex_engine == 'xelatex' else _pdflatex_header,
    )
    _doc_template_default.extend(
        [
            r'\usepackage{array}',
            r'\usepackage{tabularx}',
            r'\usepackage{xltabular}',
            r'\usepackage{booktabs}',
            r'\usepackage[table]{xcolor}',
            (
                r'\usepackage[landscape,top = 1cm,bottom = 2cm,'
                r'left = 1cm,right = 1cm]{geometry}'
            ),
            r'\newcolumntype{L}{>{\raggedright\arraybackslash}X}',
            r'\newcolumntype{K}[1]{>{\raggedright\arraybackslash}p{#1}}',
            r'\renewcommand{\arraystretch}{1.5}',
            r'\begin{document}',
            r'\fontsize{4pt}{5pt}\selectfont',
            r'\rowcolors{2}{gray!25}{white}'
            r'',
            r'%s',
            r'',
            r'\end{document}',
        ],
    )

    doc_template = (
        doc_template
            if is_str(doc_template) else  # noqa: E131
        os.linesep.join(_doc_template_default)
            if doc_template or latex_compile else  # noqa: E131
        '%s'
    )

    _ = kwargs.pop('wrap', None)

    kwargs['tablefmt'] = 'latex_%s' % ('booktabs' if booktabs else 'raw')

    tbl = table_textwrap(tbl, width = None, maxlen = maxlen)
    tbl = collections.OrderedDict(
        (
            upper0(title.replace('_', ' ')),
            column,
        ) for title, column in tbl.items()
    )

    latex_table = table_format(
        tbl = tbl, maxlen = maxlen, lineno = lineno, wrap = False, **kwargs
    )

    latex_table = latex_table.replace('tabular', 'xltabular')
    latex_table = latex_table.replace(
        r'\begin{xltabular',
        r'\begin{xltabular}{\linewidth',
    )
    recolformat = re.compile(r'(xltabular\}\{\\linewidth\}\{)(\w+)(\})')

    if not colformat:

        m = recolformat.search(latex_table)
        colformat = m.groups()[1].rsplit('r', maxsplit = 1)
        colformat = '{}r{}'.format(colformat[0], colformat[1].replace('l', 'L'))

    latex_table = recolformat.sub(r'\g<1>%s\g<3>' % colformat, latex_table)
    latex_table_head, latex_table_body = latex_table.split(
        r'\midrule',
        maxsplit = 1,
    )
    latex_table_head = os.linesep.join(
        (
            latex_table_head,
            r'\midrule',
            r'\endhead',
            '',
        ),
    )
    latex_full = doc_template % (latex_table_head + latex_table_body)
    latex_full = latex_full.replace(r'\ensuremath{<}', r'\textless ')
    latex_full = latex_full.replace(r'\ensuremath{>}', r'\textgreater ')
    latex_full = latex_full.replace(r'\_', '-')

    if not path and latex_compile:

        path = 'table-%s' % random_string()

    if path and os.path.splitext(path)[1] != '.tex':

        path = '%s.tex' % path

    if path:

        with open(path, 'w') as fp:

            fp.write(latex_full)

    if latex_compile and doc_template:

        # doing twice to make sure it compiles all right
        os.system(f'{latex_executable} {path}')
        os.system(f'{latex_executable} {path}')

    if not path:

        return latex_full


def get(obj: Iterable, field: Union[str, int]) -> Any:
    """
    Extracts elements from lists, dicts and tuples in a uniform way.

    Args:
        obj:
            An iterable of (named) tuples or lists or dicts.
        field:
            The key or index of the field.

    Returns:
        The extracted value, or `"PYPATH_NO_VALUE"` if the field does not
        exist.
    """

    return (
        getattr(obj, field) if
        (is_str(field) and hasattr(obj, field)) else obj[field] if (
            (isinstance(obj, dict) and field in obj) or
            (isinstance(obj, (tuple, list)) and isinstance(field, int))
        ) else const.NO_VALUE
    )


def values(obj: Iterable[Iterable], field: Union[int, str]) -> set:
    """
    All values of a field.

    Args:
        obj:
            An iterable of (named) tuples or lists or dicts.
        field:
            The key or index of the field.

    Returns:
        All possible unique values of the field. Unhashable values
        will be ignored.
    """

    return {
        val
        for val in (get(it, field) for it in obj)
        if (val.__hash__ is not None and val != const.NO_VALUE)
    }


def match(obj, condition):
    """
    Tests a condition on an object.

    Args:
        obj: An object to test against.
        condition: A simple value, a set of values or a callable. In the
            latter case the object will be passed to the callable, otherwise
            the ``eq`` function, defined here, will be used to match the
            object against the condition.

    Returns:
        bool: The outcome of the test.
    """

    return bool(condition(obj)) if callable(condition) else eq(obj, condition)


def filtr(obj, *args, and_or = 'AND', **kwargs):
    """
    Filters an iterable by simple conditions on one or more fields.

    Args:
        obj (iterable): An iterable of lists, (named) tuples, dicts or
            other objects.
        and_or (str):
            Whether all conditions should be met for an item to be selected
            (`AND`) or only one of them (`OR`).
        *args (tuples): The first element of each tuple is a key or index,
            the second is a condition (see details below).
        **kwargs: Names of the keyword arguments are keys or attributes,
            the values are conditions (see details below).

    Yields:
        The selected elements, which meet the conditions.

    Note:
        The conditions can be simple values or sets of values which will be
        passed to the ``eq`` function defined here. Alternatively, they
        can be callables, accepting the value of the field and returning
        bool values (otherwise the return value will be casted to bool).
        Conditions can be negated by adding one more element to the tuple,
        which should be True for negation: e.g. a tuple of
        ``(3, 'foobar', True)`` will check the index 3 in each object and
        keep those which are not equal to "foobar".
    """

    conditions = [
        (condition + (False,))[:3]
        for condition in itertools.chain(args, kwargs.items())
    ]
    _and_or = any if and_or.lower() == 'or' else all

    for it in obj:

        if _and_or(
            negate(match(get(it, field), condition), neg)
            for field, condition, neg in conditions
        ):

            yield it


def negate(value, neg = True) -> bool:
    """
    Negate a value.

    Args:
        value: Anything that can be casted to bool.
        neg (bool): Whether to negate or not. If False, the value won't be
            negated.

    Returns:
        bool: The value casted to bool and optionally negated.
    """

    return not value if neg else bool(value)


def prefix(string: str, sep: str) -> str:
    """
    Get a string prefix.

    Extracts a prefix from a string, splitting by a separator and taking
    only the first part.
    """

    return first(string.split(sep, maxsplit = 1))


def suffix(string: str, sep: str) -> str:
    """
    Get a string suffix.

    Extracts a suffix from a string, splitting by a separator and taking
    only the last part.
    """

    return first(reversed(string.rsplit(sep, maxsplit = 1)))


def remove_prefix(string: str, sep: str) -> str:
    """
    Remove a string prefix.

    Removes a prefix if `string` is a string and contains the separator
    `sep`; otherwise returns the original object.
    """

    return (
        first(reversed(string.split(sep, maxsplit = 1))) if is_str(string) else
        string
    )


def remove_suffix(string: str, sep: str) -> str:
    """
    Remove a string suffix.

    Removes a suffix if `string` is a string and contains the separator
    `sep`; otherwise returns the original object.
    """

    return string.rsplit(sep, maxsplit = 1)[0] if is_str(string) else string


def maybe_in_dict(dct: dict, key: Any) -> Any:
    """
    Translate by dict if possible.

    Retrieves a key from a dict if the key is in the dict, otherwise
    returns the key itself.
    """

    return dct.get(key, key)


def decode(string: Any, *args, **kwargs) -> Any:
    """
    Decodes a string if it is a byte string, otherwise returns it unchanged.

    Args:
        string:
            A string, either a byte string or a decoded string.
        args, kwargs:
            Passed to `bytes.decode`, it accepts two arguments:
            `encoding` and `errors`.

    Returns:
        A decoded string.
    """

    if hasattr(string, 'decode'):

        string = string.decode(*args, **kwargs)

    return string


def identity(obj: Any) -> Any:
    """
    Do nothing, returns the object unchanged.
    """

    return obj


def nest(*funcs: Callable) -> Callable:
    """
    Nest multiple functions into a single function.
    """

    return lambda x: functools.reduce(lambda x, f: f(x), (x,) + funcs)


def compr(
        obj: Iterable | dict,
        apply: Callable | None = None,
        filter: Callable | None = None,
) -> Iterable | dict:
    """
    Unified interface for list, dict, set and tuple comprehensions.

    Args:
        obj:
            An iterable, a dict or a set or a tuple.
        apply:
            A function to apply to each element of the iterable or dict.
        filter:
            A function to filter elements of the iterable or dict.
            For filtering by equality or incidence, provide a simple
            object or an array.

    Returns:
        Same type as the input: a list, a dict or a set or a tuple.
    """

    _type = (
        dict
            if isinstance(obj, Mapping) else
        type(obj)
            if isinstance(obj, Iterable) and not isinstance(obj, Iterator) else
        list
    )

    apply = apply or identity
    extract = (lambda x: x[1]) if _type == dict else identity
    process = nest(extract, apply)
    insert = (lambda x: (x[0], process(x))) if _type == dict else process

    filter = (
        filter
            if callable(filter) else
        to_set(filter).__contains__
            if isinstance(filter, const.LIST_LIKE) else
        filter.__eq__
    )

    filter = nest(extract, filter)
    obj = obj.items() if _type == dict else obj

    return _type(insert(it) for it in obj if filter(it))


def ignore_unhashable(func):
    """
    Decorator to ignore unhashable values.

    This is useful when using `lru_cache` on functions with optionally
    unhashable arguments.

    Based on https://stackoverflow.com/a/64111268/854988.
    """

    uncached = func.__wrapped__
    attributes = functools.WRAPPER_ASSIGNMENTS + ('cache_info', 'cache_clear')

    @functools.wraps(func, assigned = attributes)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError as error:
            if 'unhashable type' in str(error):
                return uncached(*args, **kwargs)
            raise

    wrapper.__uncached__ = uncached

    return wrapper


def from_module(what: str) -> Callable | types.ModuleType | None:
    """
    Access an object or submodule from a module.

    Args:
        what:
            Path to the target in dot separated style, e.g. ``foo.bar.baz``
            will return the ``baz`` object from ``foo.bar`` module.

    Returns:
        The requested attribute if successful, otherwise None.
    """

    mod, attr = what.rsplit('.', maxsplit = 1)

    try:

        _mod = __import__(mod)
        return getattr(_mod, attr)

    except ModuleNotFoundError:

        return getattr(from_module(mod), attr)


def code_to_func(code: str) -> Callable:
    """
    Convert a Python code string to a function.

    Args:
        code:
            Code of a function definition.

    Returns:
        The function.
    """

    bytecode = compile(code, '<string>', 'exec')
    ns = {}
    eval(bytecode, {}, ns)

    return first(ns.values())

"""
General helper functions for processing Python data structures.
"""

import pypath_common._constants as const

__all__ = [
    'swap_dict',
]


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

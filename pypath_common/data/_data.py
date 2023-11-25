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

"""
Access built-in data in this and other modules.

The files are looked up in the `data` or `_data` directory of the calling
module by default and read by the reader function provided, or the default
reader functions defined in `_FORMATS`.
"""

from __future__ import annotations

from typing import Any, Callable
import os
import pathlib as pl
import functools

import yaml

import pypath_common._misc as _misc
import pypath_common._session as _session

__all__ = [
    'builtins',
    'load',
    'path',
]

_log = lambda x: _session.logger(name = 'pypath_common.data').log(x)

_FORMATS = {
    'json': 'json.load',
    'yaml': functools.partial(yaml.load, Loader = yaml.FullLoader),
    'csv': 'pandas.read_csv',
    'tsv': 'pandas.read_csv',
    'xml': _misc.identity,
    'txt': None,
    'sql': None,
    '': None,
    'html': _misc.identity,
    'ico': _misc.identity,
}


def path(label: str, module: str | None = None) -> pl.Path | None:
    """
    Find path to data shipped with a module.

    Args:
        label:
            Label of a built-in dataset or path to a file.
        module:
            Name of the module the built-in data is shipped with.

    Returns:
        A path to the module data, None if not found.
    """

    if os.path.exists(label):

        path = pl.Path(label).absolute()

    else:

        available = builtins(module)
        path = available.get(label, None)
        path = path or available.get(_misc.remove_suffix(label, '.'), None)

    return path


def load(
        label: str,
        module: str | None = None,
        reader: Callable | None = None,
        **kwargs
) -> Any:
    """
    Load data shipped with the module or data from a path.

    Args:
        label:
            Label of a built-in dataset or path to a file.
        module:
            Name of the module the built-in data is shipped with.
        reader:
            A function to read the file.
        kwargs:
            Parameters for to the reader function.

    Returns:
        The object read from the file (typically a dict or list).
    """

    module = module or _misc.caller_module()

    if _path := path(label, module):

        if not reader:

            ext = _path.name.rsplit('.', maxsplit = 1)[-1].lower()
            if ext == 'tsv':
                kwargs['sep'] = '\t'
            reader = _FORMATS.get(ext, lambda x: x.readlines())

        if not callable(reader):

            reader = _misc.from_module(reader)

        _log(
            f'Loading built-in data `{label}` from module `{module}`; '
            f'path: `{_path}`.',
        )

        with open(_path) as fp:

            return reader(fp, **kwargs)

    else:

        _log(f'Could not find built-in data `{label}` in module `{module}`.')


def builtins(module: str | None = None) -> dict[str, str]:
    """
    List of built-in datasets.

    Args:
        module:
            Name of the module the built-in data is shipped with. By default
            the calling module will be used.

    Returns:
        A dict of files within the module's data directory, if it exists.
        Keys are file names (including subdirectory paths within the data
        directory), values are the full paths.
    """

    module = module or _misc.caller_module()
    datadir = _misc.module_datadir(module)

    return {
        str((pl.Path(d) / pl.Path(f).stem).relative_to(datadir)):
        pl.Path(d) / f
        for d, dirs, files in os.walk(datadir)
        for f in files
        if pl.Path(f).suffix[1:].lower() in _FORMATS
    }

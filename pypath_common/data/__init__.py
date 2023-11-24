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
Data shared across pypath modules.

Data about resource specific vocabularies, generic data for molecular biology
data processing, module settings. Stored in YAML, JSON, TSV or other formats.
This module also supports the access to built in data in other modules.
"""

from pypath_common.data._data import load, path, builtins

__all__ = ['builtins', 'load', 'path']

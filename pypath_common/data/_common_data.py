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
Built-in data in this module.
"""

from __future__ import annotations

import functools

from pypath_common._process import swap_dict
from . import _data

__all__ = [
    'aacodes',
    'aaletters',
    'aanames',
    'amino_acids',
    'aminoa_1_to_3_letter',
    'aminoa_3_to_1_letter',
    'igraph_graphics_attrs',
    'mod_keywords',
    'pmod_bel',
    'pmod_bel_to_other',
    'pmod_other_to_bel',
    'psite_mod_types',
    'psite_mod_types2',
]

_common_data = functools.partial(_data.load, module = 'pypath_common')


def aacodes() -> dict[str, str]:
    """
    Mapping between single letter and three letters amino acid codes.
    """

    return _common_data('aacodes')


def aanames() -> dict[str, str]:
    """
    Mapping between common names and single letter codes of amino acids.
    """

    return _common_data('aanames')


def mod_keywords() -> dict[str, list]:
    """
    Resource specific post-translational modification name patterns.
    """

    return _common_data('mod_keywords')


def aaletters() -> dict[str, str]:
    """
    Mapping between three letters and single letter amino acid codes.
    """
    return swap_dict(aacodes())


def igraph_graphics_attrs() -> dict[str, list]:
    """
    Igraph graphics parameters for edges and vertices.
    """

    return _common_data('igraph_graphics_attrs')


def psite_mod_types() -> list[tuple[str, str]]:
    """
    PhosphoSite PTM type codes.
    """  # noqa: D403

    return _common_data('psite_mod_types')


def psite_mod_types2() -> list[tuple[str, str]]:
    """
    PhosphoSite PTM type codes, version 2.
    """  # noqa: D403

    return _common_data('psite_mod_types2')


def pmod_bel() -> tuple[tuple[str, tuple[str]]]:
    """
    BEL (Biological Expression Language) PTM type codes and keywords.
    """

    return _common_data('pmod_bel')


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

    return _common_data('amino_acids')


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

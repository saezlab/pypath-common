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
data processing, module settings. Stored in YAML or JSON.
"""

from typing import Any
import os

import yaml

__all__ = ['module_data']


def module_data(name: str) -> Any:
    """
    Retrieve the contents of a YAML file shipped with this module.
    """

    here = os.path.dirname(os.path.abspath(__file__))

    path = os.path.join(here, f'{name}.yaml')

    if os.path.exists(path):

        with open(path) as fp:

            return yaml.load(fp.read(), Loader = yaml.FullLoader)

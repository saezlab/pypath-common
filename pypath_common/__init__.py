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
Code shared across pypath modules.
"""

__author__ = ', '.join(['Dénes Türei'])
__maintainer__ = ', '.join(['Dénes Türei'])
__version__ = '0.2.0'
__email__ = 'turei.denes@gmail.com'

from pypath_common import data
from pypath_common import _misc as misc  # noqa: F401
from pypath_common import _constants as const
from pypath_common._session import Logger, log, logger, session  # noqa: F401

PYPATH_SESSION = session('pypath', paths = 'pypath_common')
pypath_log = PYPATH_SESSION.log

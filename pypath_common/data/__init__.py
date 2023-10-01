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

        with open(path, 'r') as fp:

            return yaml.load(fp.read(), Loader=yaml.FullLoader)

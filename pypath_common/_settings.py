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
A simple settings (config) manager.
"""

from types import MappingProxyType
from typing import Any, Optional
import os
import sys
import contextlib

import yaml

__all__ = ['Settings']


class Settings:
    """
    Manage settings for other modules.
    """

    def __init__(
        self,
        fname: Optional[str] = None,
        module: Optional[str] = None,
        _dict: Optional[dict] = None,
        **kwargs,
    ):
        """
        Create a collection of settings.

        Args:
            fname:
                Path to a YAML config file.
            module:
                Name of the module.
            _dict:
                Settings as a dictionary.
            kwargs:
                Key-value pairs to be included in the settings dict
        """

        self.fname = fname
        self.module = module
        self._config_from_module()
        self.reset_all()
        self.setup(_dict, **kwargs)
        self._context_settings = []

    def config_file_contents(self) -> dict:
        """
        Read the contents of the YAML config file.

        Returns:
            A dict with the config read from the YAML or an empty dict if
            config file was not provided or does not exist.
        """

        config = {}

        if self.fname and os.path.exists(self.fname):

            with open(self.fname) as fp:

                config = yaml.load(fp, Loader = yaml.FullLoader)

        return config

    @property
    def _module_basedir(self):

        if self.module:

            mod = sys.modules[self.module]

            if mod:

                mod_path = os.path.abspath(os.path.dirname(mod.__file__))
                mod_dir = os.path.join(*os.path.split(mod_path)[:-1])

                return mod_dir

    @property
    def _module_datadir(self):

        mod_dir = self._module_basedir

        if mod_dir:

            return os.path.join(mod_dir, 'data')

    def _config_from_module(self):

        datadir = self._module_datadir

        if not self.fname and datadir:

            module_fname = os.path.join(datadir, 'settings.yaml')

            if os.path.exists(module_fname):

                self.fname = module_fname

    def reset_all(self):
        """
        Set the values of all parameters to their defaults.
        """

        self._settings = {}
        self._context_settings = []

        from_config = self.config_file_contents()
        in_datadir = from_config.get('in_datadir', ())
        datadir = from_config.get('datadir', self._module_datadir) or 'data'

        self.setup(
            {  # noqa: C402
                k: os.path.join(datadir, val) if k in in_datadir else val
                for k, val in from_config.items()
            },
        )

        # runtime attributes
        self.setup(
            module = self.module,
            basedir = self._module_basedir,
        )

        self._defaults = MappingProxyType(self.as_dict)

    def setup(self, _dict = None, **kwargs):
        """
        Set the values of various parameters in the settings.

        Args:
            _dict: A `dict` of parameters, keys are the option names, values
                are the values to be set.
            kwargs: Alternative way to provide parameters, argument names
                are the option names, values are the corresponding values.

        Returns:
            None
        """

        _dict = self._dict_and_kwargs(_dict, kwargs)
        self._settings.update(_dict)

    @staticmethod
    def _dict_and_kwargs(_dict, kwargs):

        _dict = _dict or {}
        _dict.update(kwargs)

        return _dict

    def get(self, param, override = None, default = None):
        """
        Retrieves the current value of a parameter.

        :param str param:
            The key for the parameter.
        :param object,NoneType override:
            If this value is not None it will be returned instead of the
            settings value. It is useful if the parameter provided at the
            class or method level should override the one in settings.
        :param object,NoneType default:
            If no value is available for the parameter in the current
            settings, this default value will be returned instead.
        """

        return (
            (self[param] if param in self else default)
            if override is None
            else override
        )

    def default(self, param: str) -> Any:
        """
        Default value of a parameter.

        Args:
            param:
                The name of the parameter.

        Returns:
            The default value of the parameter or None.
        """

        return self._defaults.get(param)

    @property
    def contexts(self) -> list[dict]:
        """
        A list of active context specific settings (used in *with* statements).

        Returns:
            Each dict in the returned list corresponds to an active context,
            the first one is the innetmost.
        """

        return reversed(self._context_settings)

    def _from_context(self, param):

        for ctx in self.contexts:

            if param in ctx:

                return ctx[param]

    def _in_context(self, param):

        return any(param in ctx for ctx in self.contexts)

    @contextlib.contextmanager
    def context(self, _dict: Optional[dict] = None, **kwargs):
        """
        Temporarily alter the values of certain parameters.

        At exiting the context, the original values will be restored.
        Multiple contexts can be nested within each other.

        Args:
            _dict: A `dict` of parameters, keys are the option names, values
                are their values.
            kwargs: Alternative way to provide parameters, argument names
                are the option names, values are the corresponding values.
        """

        try:

            ctx = self._dict_and_kwargs(_dict, kwargs)
            self._context_settings.append(ctx)
            yield

        finally:

            self._context_settings = self._context_settings[:-1]

    @property
    def _numof_contexts(self):

        return len(self._context_settings)

    @property
    def _innermost_context(self):

        return self._context_settings[-1] if self._context_settings else None

    def reset(self, param: str):
        """
        Reset a parameter to its default value.

        Args:
            param:
                The name of the parameter to be reset.
        """

        self.setup({param: self.default(param)})

    def __getattr__(self, attr):

        if attr in self:

            return self[attr]

        elif attr in self.__dict__:

            return self.__dict__[attr]

        else:

            raise AttributeError(
                "'%s' object has no attribute '%s'"
                % (self.__class__.__name__, str(attr)),
            )

    def __dir__(self):

        keys = object.__dir__(self)
        [keys.extend(ctx.keys()) for ctx in self.contexts]
        keys.extend(self._settings.keys())
        keys = sorted(set(keys))

        return keys

    def __contains__(self, param):

        return self._in_context(param) or param in self._settings

    def __getitem__(self, key):

        if self._in_context(key):

            return self._from_context(key)

        elif key in self._settings:

            return self._settings[key]

        else:

            return None

    def __setitem__(self, key, value):

        self._settings[key] = value

    @property
    def as_dict(self) -> dict:
        """
        This settings instance as a dict.
        """

        return self._settings.copy()

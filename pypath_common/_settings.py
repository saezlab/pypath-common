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

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Iterable
import os
import re
import pathlib as pl
import itertools
import contextlib

import yaml
import platformdirs

import pypath_common._misc as _misc

__all__ = ['Settings']


class Settings:
    """
    Manage settings for other modules.
    """

    _EXTENSIONS = ('yaml', 'yml')
    _NAME_STEMS = ('settings', 'config')

    def __init__(
        self,
        paths: str | Iterable[str] | None = None,
        module: str | None = None,
        author: str | None = None,
        _dict: dict | None = None,
        **kwargs,
    ):
        """
        Create a collection of settings.

        Args:
            paths:
                Paths to one or more YAML config files, in order of priority.
                Alternatively, it can be a one or more module names, in this
                case the config file will be looked up in these modules.
            module:
                Name of the module.
            _dict:
                Settings as a dictionary.
            kwargs:
                Key-value pairs to be included in the settings dict
        """

        self._paths = _misc.to_list(paths)
        self.module = module
        self.author = author
        self._custom_paths()
        self._read_defaults()
        self.reset_all()
        self.setup(_dict, **kwargs)


    def _bootstrap(self):

        self._parsed = []

        for path in reversed(self.paths):

            if os.path.exists(path) and path not in self._parsed:

                self._parsed.append(path)
                self.setup(self.read(path))

        self._setup_datadir()
        self._setup_cachedir()
        self._setup_secretsdir()
        self._finish_defaults()


    @staticmethod
    def read(path: str | pl.Path) -> dict:
        """
        Read the contents of one YAML config file.

        Returns:
            A dict with the config read from the YAML or an empty dict if
            config file was not provided or does not exist.
        """

        config = {}

        if path and os.path.exists(path):

            with open(path) as fp:

                config = yaml.load(fp, Loader = yaml.FullLoader)

        return config


    @property
    def _module_basedir(self) -> pl.Path | None:

        if self.module:

            return _misc.module_path(self.module)


    @property
    def _module_datadir(self) -> str | None:

        mod_dir = self._module_basedir

        if mod_dir:

            return os.path.join(mod_dir, 'data')


    @property
    def _user_config_dir(self) -> str | None:

        return platformdirs.user_config_dir(self.module, self.author)


    @property
    def _user_cache_dir(self) -> str | None:

        return platformdirs.user_cache_dir(self.module, self.author)


    @property
    def _user_secrets_dir(self) -> str | None:

        return os.path.join(self._user_config_dir, 'secrets')


    @property
    def _old_user_config_dir(self) -> str | None:

        return os.path.join(os.path.expanduser('~'), f'.{self.module}')


    @property
    def _directories(self) -> tuple[str]:
        """
        Directories where to look for config files.

        Includes three directories: the working directory, the user config
        directory and the module's built in default config, hence a three
        element tuple is returned.
        """

        return (
            os.getcwd(),
            self._user_config_dir,
            self._old_user_config_dir,
            self._module_datadir,
        )


    @property
    def _fname_stems(self) -> list[str]:

        with_modname = [
            sep.join(rev((self.module, stem)))
            for stem, sep in itertools.product(self._NAME_STEMS, ('-', '_'))
            for rev in (_misc.identity, reversed)
        ] if self.module else []

        return list(self._NAME_STEMS) + with_modname


    @property
    def _fnames(self) -> list[str]:

        return [
            os.path.extsep.join((stem, ext))
            for stem in self._fname_stems
            for ext in self._EXTENSIONS
        ]


    def paths_in(
            self,
            wd: bool = True,
            user: bool = True,
            old_user: bool = True,
            builtin = True,
    ) -> list[pl.Path]:
        """
        All possible config paths from the requested directories.

        Args:
            wd:
                Include paths in the current working directory.
            user:
                Include paths in the user config directory.
            old_user:
                Include paths in the old user config directory
                (``~/.pypath``).
            builtin:
                Include paths in the module's built in directory.

        Returns:
            A list of paths covering all possible directories, file names and
            extensions.
        """

        directories = (
            self._other_modules +
            [
                d for d, e in zip(
                    self._directories,
                    (wd, user, old_user, builtin),
                )
                if e
            ]
        )

        return [
            pl.Path(d) / f
            for d in directories
            for f in self._fnames
            if d
        ]


    def _custom_paths(self):

        paths = []
        modules = []

        for path in self._paths:

            if not os.path.isfile(path) and re.match(r'[\w\.]+', str(path)):

                mod_path = _misc.module_path(str(path))
                modules.append(mod_path)

                for datadir in ('data', '_data'):

                    if (mod_data_path := mod_path / datadir).exists():

                        modules.append(mod_data_path)

            else:

                paths.append(pl.Path(path))

        self._paths = paths
        self._other_modules = _misc.to_list(self._other_modules) + modules


    @property
    def paths(self) -> list[pl.Path]:
        """
        All possible config paths.
        """

        return self._paths + self.paths_in()


    def _read_defaults(self):

        result = {}
        datadirs = _misc.to_list(self._module_datadir) + self._other_modules

        for datadir, fname in itertools.product(datadirs, self._fnames):

            if module_fname := os.path.join(datadir, fname):

                result = self.read(module_fname)
                break

        self._module_defaults = result


    def reset_all(self):
        """
        Set the values of all parameters to their defaults.
        """

        self._settings = {}
        self._context_settings = []
        self._bootstrap()


    def _setup_datadir(self, override: str | None = None):

        in_datadir = self.get('in_datadir', default = ())
        datadir = self.get(
            'datadir',
            override = override,
            default = self._module_datadir or 'data',
        )
        self.setup(
            {  # noqa: C402
                k: os.path.join(datadir, p)
                for k, p in ((k, self.get(k)) for k in in_datadir)
                if os.path.dirname(p) != datadir
            },
        )

        # runtime attributes
        self.setup(
            datadir = datadir,
            module = self.module,
            basedir = self._module_basedir,
        )


    def _finish_defaults(self):

        self._defaults = MappingProxyType(self.as_dict)


    def _setup_cachedir(self):

        cachedir = self._setup_dir('cachedir')

        if not self.get('pickle_dir'):

            self.setup(pickle_dir = os.path.join(cachedir, 'pickles'))
            os.makedirs(self.get('pickle_dir'), exist_ok = True)


    def _setup_secretsdir(self):

        self._setup_dir('secrets_dir')


    def _setup_dir(self, key: str) -> str:

        default = f'_user_{key[:-3].strip("_")}_dir'
        path = self.get(key) or getattr(self, default)
        self.setup({key: path})

        for key in self.get(f'in_{key}', default = ()):  # noqa: B020

            if not os.path.dirname(fname := self.get(key)):

                self.setup({key: os.path.join(path, fname)})

        os.makedirs(path, exist_ok = True)

        return path


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
            (default if self[param] is None else self[param])
            if override is None
            else override
        )


    def default(self, param: str) -> Any:
        """
        Default value of a parameter as read from the config files.

        Args:
            param:
                The name of the parameter.

        Returns:
            The default value of the parameter or None.
        """

        return self._defaults.get(param)


    def builtin_default(self, param: str) -> Any:
        """
        The built-in default value of a parameter.

        Args:
            param:
                The name of the parameter.

        Returns:
            The default value of the parameter or None.
        """

        return self._module_defaults.get(param, None)


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

        return any(
            param in ctx
            for ctx in self.__dict__.get('_context_settings', {})
        )


    @contextlib.contextmanager
    def context(self, _dict: dict | None = None, **kwargs):
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


    def __dir__(self):

        keys = object.__dir__(self)
        [keys.extend(ctx.keys()) for ctx in self.contexts]
        keys.extend(self._settings.keys())
        keys = sorted(set(keys))

        return keys


    def __contains__(self, param):

        return (
            self._in_context(param) or
            param in self.__dict__.get('_settings', {})
        )


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

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

from __future__ import annotations

from typing import Union, Optional
import os
import sys
import builtins
import itertools
import traceback

from pypath_common import _misc, _logger, _settings

__all__ = [
    'Logger',
    'ManagedLogger',
    'SESSIONS',
    'Session',
    'config',
    'log',
    'logger',
    'new_session',
    'session',
    'session_logger',
]

SESSIONS = globals().get('SESSIONS', {})


class Session:
    """
    Session manager.
    """

    def __init__(
        self,
        module: Optional[str] = None,
        label: Optional[str] = None,
        log_verbosity: Optional[int] = None,
        logdir: Optional[str] = None,
        config: Optional[Union[dict, str]] = None,
        **kwargs,
    ):
        """
        Start a new session.

        Args:
            module:
                Name of the module the session belongs to.
            label:
                Name of the session. If not provided, a random string will be
                used.
            log_verbosity:
                Default log verbosity for the session.
            logdir:
                Directory for log files.
            config:
                Path to the config file or config as a dict.
            kwargs:
                Configuration key-value pairs.
        """

        self.module = _get_module(module)
        self.module_root = _misc.module_path(self.module)
        self.label = label or self.gen_session_id()
        self.logdir = logdir

        config_fname = config if isinstance(config, str) else None
        config_dict = None if config_fname else config
        kwargs['paths'] = (
            _misc.to_list(kwargs.get('paths', [])) +
            _misc.to_list(config_fname)
        )

        self.config = _settings.Settings(
            module = self.module,
            _dict = config_dict,
            **kwargs
        )
        self.log_verbosity = _misc.first_value(
            log_verbosity,
            self.config.get('log_verbosity'),
        )

        self.start_logger()
        self._logger.msg('Session `%s` started.' % self.label)
        self._logger.msg('Config has been read from the following files:')
        [self._logger.msg(f'  - {path}') for path in self.config._parsed]


    @staticmethod
    def gen_session_id(length: int = 5) -> str:
        """
        Get a new session identifier.

        Args:
            length:
                Length of the identifier.

        Returns:
            A random identifier of alphanumeric characters.
        """

        return _misc.random_string(length)


    def start_logger(self):
        """
        Start the logger.

        Creates a logger for this session which will be served to all modules.
        """

        self.logfile = str(
            os.getenv('PYPATH_LOG') or
            getattr(builtins, 'PYPATH_LOG', None) or
            'pypath-%s.log' % self.label,
        )

        self._logger = _logger.Logger(
            fname = os.path.basename(self.logfile),
            settings = self.config,
            verbosity = self.log_verbosity,
            logdir = os.path.dirname(self.logfile),
        )
        self._managed_loggers = {}


    def finish_logger(self):
        """
        Close the logger.
        """

        self._logger.msg('Session `%s` finished.' % self.label)
        self._logger.close_logfile()


    def __repr__(self):

        return '<Session %s>' % self.label


    def __del__(self):

        if hasattr(self, '_logger'):

            self._logger.msg('Session `%s` finished.' % self.label)


    def get(self, param, override = None):
        """
        The current value of a settings parameter.

        Args:
            param (str): Name of a parameter.
            override: Override the currently valid settings,
                return this value instead.
            default: If no value is set up for the key requested,
                use this default value instead.

        Wrapper of `Settings.get()`.
        """
        return self.config.get(param, override = override)


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

        return self.config.setup(_dict, **kwargs)


    def context(self, _dict: Optional[dict] = None, **kwargs):
        """
        Context with altered settings.

        Args:
            _dict:
                A dictionary of config key-value pairs.
            kwargs:
                Config key-value pairs.
        """

        return self.config.context(_dict, **kwargs)


    def logger(self, name: str | None) -> Logger:
        """
        Access a logger with the given name.

        Args:
            name:
                Name of the logger, this will be included in front of each
                message from this logger. If not provided, the default logger
                of this session will be returned.

        These are loggers managed by this session instance, in contrast to
        other loggers that are created by inheritance.
        """

        name = name or self.module

        if name not in self._managed_loggers:

            self._managed_loggers[name] = ManagedLogger(name = name)

        return self._managed_loggers[name]


    def log(self, msg: str = '', level: int = 0, name: str | None = None):
        """
        Send a log message.

        Args:
            msg:
                Text of the message.
            level:
                Priority level of the message.
            name:
                Name of the logger, this will be included in front of each
                message from this logger. If not provided, the default logger
                of this session will be returned.
        """

        self.logger(name).log(msg = msg, level = level)


class Logger:
    """
    Base class that makes logging available for its descendants.
    """

    def __init__(self, name: str | None = None, module: str | None = None):
        """
        Make this instance a logger.

        Args:
            name:
                The label of this instance that will be prepended to all
                messages it sends to the logger.
            module:
                Send the messages by the logger of this module.
        """

        self._log_name = name or self.__class__.__name__
        self._logger = session_logger(module = module)


    def _log(self, msg = '', level = 0):
        """
        Write a message into the logfile.
        """

        self._logger.msg(msg = msg, label = self._log_name, level = level)


    def _console(self, msg = ''):
        """
        Write a message to the console and also to the logfile.
        """

        self._logger.console(msg = msg, label = self._log_name)


    def _log_traceback(self, console: bool = False):
        """
        Include a traceback into the log.
        """

        exc_type, exc_value, exc_traceback = sys.exc_info()

        if exc_type is not None:

            f = exc_traceback.tb_frame.f_back
            stack = traceback.extract_stack(f)

        else:

            stack = traceback.extract_stack()[:-1]

        trc = 'Traceback (most recent call last):\n'
        trc_list = list(
            itertools.chain(
                *(
                    stack_level.strip('\n').split('\n')
                    for stack_level in traceback.format_list(stack)
                )
            ),
        )

        if exc_type is not None:

            trc_list.extend(
                ('  %s' % traceback.format_exc().lstrip(trc)).split('\n'),
            )

        stack_top = 0

        for i, line in enumerate(trc_list):

            if line.strip().endswith('<module>'):

                stack_top = i

        trc_list = trc_list[stack_top:]

        write = self._console if console else self._log

        write(trc.strip())

        for traceline in trc_list:

            write(traceline)


class ManagedLogger(Logger):
    """
    A stand alone logger that is managed by a session instance.
    """

    log = Logger._log
    console = Logger._console
    log_traceback = Logger._log_traceback


def _get_module(
        module: str | None = None,
        top: bool = False,
) -> str:
    """
    The first module in the call stack outside of this module.

    Args:
        module:
            Override the name of the module instead of getting it from
            some parent frame.
        top:
            Return only the top level module, without submodules.

    Returns:
        The name of the module of the caller ``level`` frames above.
    """

    module = module or _misc.caller_module(with_submodules = not top)

    if module == 'pypath_common':

        module = 'pypath'

    return module


def session(module: Optional[str] = None, **kwargs) -> Session:
    """
    Create new session or return the one already created.

    Args:
        module:
            Name of the module the session belongs to.
        kawrgs:
            Passed to `Session`.

    Returns:
        The session of the module.
    """

    module = _get_module(module, top = True)

    if module not in SESSIONS:

        new_session(module = module, **kwargs)

    return SESSIONS[module]


def session_logger(module: Optional[str] = None) -> _logger.Logger:
    """
    Get the `Logger` instance of the session.

    Args:
        module:
            Name of the module the session belongs to.

    Returns:
        The Logger instance of the session.
    """

    return session(module = module)._logger


def config(module: Optional[str] = None) -> _settings.Settings:
    """
    Get the configuration of a session.

    The config contains user controlled parameters of a module.

    Args:
        module:
            Name of the module the session belongs to.

    Returns:
        A `_settings.Settings` instance.
    """

    return session(module = module).config


def new_session(
    module: str,
    **kwargs,
):
    """
    Create a new session.

    In case a session already exists it will be deleted.

    Args:
        module:
            Name of the module the session belongs to.
        kwargs:
            Passed to `Session`.
    """

    SESSIONS[module] = Session(module, **kwargs)


def logger(name: str, module: str | None = None) -> ManagedLogger:
    """
    Retrieve a logger managed by a session by its name.

    Args:
        name:
            Name of the logger.
        module:
            Module the session belongs to.
    """

    return session(module).logger(name = name)


def log(
        msg: str = '',
        level: int = 0,
        name: str | None = None,
        module: str | None = None,
):
    """
    Send a log message.

    Args:
        msg:
            Text of the message.
        level:
            Priority level of the message.
        module:
            Send the message by the logger of this module.
    """

    session(module).log(msg = msg, level = level, name = name)

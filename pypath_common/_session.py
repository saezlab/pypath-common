#!/usr/bin/env python

#
#  This file is part of the `pypath` python module
#
#  Copyright
#  2014-2022
#  EMBL, EMBL-EBI, Uniklinik RWTH Aachen, Heidelberg University
#
#  Authors: Dénes Türei (turei.denes@gmail.com)
#           Nicolàs Palacio
#           Sebastian Lobentanzer
#           Erva Ulusoy
#           Olga Ivanova
#           Ahmet Rifaioglu
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  Website: http://pypath.omnipathdb.org/
#

from typing import Union, Optional
import sys
import random
import itertools
import traceback

from pypath_common import _logger

__all__ = ["Session", "Logger", "get_session", "new_session", "get_log"]

SESSIONS = globals().get("SESSIONS", {})


class Session:
    """
    Session manager.
    """

    def __init__(
        self,
        module: Optional[str] = None,
        label: Optional[str] = None,
        log_verbosity: int = 0,
        logdir: Optional[str] = None,
        config: Optional[Union[dict, str]] = None,
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
        """

        self.module = _get_module(module)
        self.label = label or self.gen_session_id()
        self.log_verbosity = log_verbosity
        self.logdir = logdir
        self.start_logger()
        self.log.msg("Session `%s` started." % self.label)

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

        abc = "0123456789abcdefghijklmnopqrstuvwxyz"
        return "".join(random.choice(abc) for i in range(length))

    def start_logger(self):
        """
        Start the logger.

        Creates a logger for this session which will be served to all modules.
        """

        self.logfile = f"{self.module}-{self.label}.log"
        self.logdir = self.logdir or "%s_log" % self.module
        self.log = _logger.Logger(
            fname=self.logfile,
            logdir=self.logdir,
            verbosity=self.log_verbosity,
        )

    def finish_logger(self):
        """
        Close the logger.
        """

        self.log.close_logfile()
        self.log.msg("Session `%s` finished." % self.label)

    def __repr__(self):

        return "<Session %s>" % self.label

    def __del__(self):

        if hasattr(self, "log"):

            self.log.msg("Session `%s` finished." % self.label)


class Logger:
    """
    Base class that makes logging available for its descendants.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Make this instance a logger.

        Args:
            name:
                The label of this instance that will be prepended to all
                messages it sends to the logger.
        """

        self._log_name = name or self.__class__.__name__
        self._logger = get_log()

    def _log(self, msg="", level=0):
        """
        Write a message into the logfile.
        """

        self._logger.msg(msg=msg, label=self._log_name, level=level)

    def _console(self, msg=""):
        """
        Write a message to the console and also to the logfile.
        """

        self._logger.console(msg=msg, label=self._log_name)

    def _log_traceback(self):
        """
        Include a traceback into the log.
        """

        exc_type, exc_value, exc_traceback = sys.exc_info()

        if exc_type is not None:

            f = exc_traceback.tb_frame.f_back
            stack = traceback.extract_stack(f)

        else:

            stack = traceback.extract_stack()[:-1]

        trc = "Traceback (most recent call last):\n"
        trc_list = list(
            itertools.chain(
                *(
                    stack_level.strip("\n").split("\n")
                    for stack_level in traceback.format_list(stack)
                )
            )
        )

        if exc_type is not None:

            trc_list.extend(
                ("  %s" % traceback.format_exc().lstrip(trc)).split("\n")
            )

        stack_top = 0

        for i, line in enumerate(trc_list):

            if line.strip().endswith("<module>"):

                stack_top = i

        trc_list = trc_list[stack_top:]

        self._log(trc.strip())

        for traceline in trc_list:

            self._log(traceline)


def _get_module(module: Optional[str] = None, level: int = 2) -> str:
    """
    The module some frames above.

    Should be called from a function that is called directly from the
    client module.

    Args:
        module:
            Override the name of the module instead of getting it from
            some parent frame.
        level:
            How many frames above get the module from.

    Returns:
        The name of the module of the caller ``level`` frames above.
    """

    return module or sys._getframe(level).f_back.f_globals["__name__"]


def get_session(module: Optional[str] = None, **kwargs) -> Session:
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

    module = _get_module(module)

    if module not in SESSIONS:

        new_session(module=module, **kwargs)

    return SESSIONS[module]


def get_log(module: Optional[str] = None) -> Logger:
    """
    Get the ``Logger`` instance of the session.

    Args:
        module:
            Name of the module the session belongs to.

    Returns:
        The Logger instance of the session.
    """

    module = _get_module(module)

    return get_session(module=module).log


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

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

from typing import Optional
import sys
import random
import itertools
import traceback

from pypath_common import _logger

__all__ = ["Session", "Logger"]


class Session:
    """
    Session manager.
    """

    def __init__(self, label: Optional[str] = None, log_verbosity: int = 0):
        """
        Start a new session.

        Args:
            label:
                Name of the session. If not provided, a random string will be
                used.
            log_verbosity:
                Default log verbosity for the session.
        """

        self.label = label or self.gen_session_id()
        self.log_verbosity = log_verbosity
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

        self.logfile = "pypath-%s.log" % self.label
        self.log = _logger.Logger(self.logfile, verbosity=self.log_verbosity)

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


def get_session():
    """
    Create new session or return the one already created.
    """

    mod = sys.modules[__name__]

    if not hasattr(mod, "session"):

        new_session()

    return sys.modules[__name__].session


def get_log():
    """
    Get the ``Logger`` instance belonging to the session.
    """

    return get_session().log


def new_session(label: Optional[str] = None, log_verbosity: int = 0):
    """
    Create a new session.

    In case a session already exists it will be deleted.

    Args:
        label:
            A custom name for the session.
        log_verbosity:
            Verbosity level passed to the logger.
    """

    mod = sys.modules[__name__]

    if hasattr(mod, "session"):

        delattr(mod, "session")

    mod.session = Session(label, log_verbosity)

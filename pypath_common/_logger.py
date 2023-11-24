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

from typing import TYPE_CHECKING, Optional
import os
import sys
import time
import pydoc
import datetime
import textwrap

import timeloop

__all__ = ['new_logger', 'Logger']


_log_flush_timeloop = timeloop.Timeloop()
_log_flush_timeloop.logger.setLevel(9999)

if TYPE_CHECKING:

    from ._settings import Settings


def new_logger(
    name: str,
    settings: 'Settings',
    logdir: Optional[str] = None,
    verbosity: Optional[int] = None,
    **kwargs,
):
    """
    Returns a new logger with default settings (can be customized).

    Args:
        name : str
            Custom name for the log.
        settings:
            The ``Settings`` instance of the module.
        logdir : str
            Path to the directoty to store log files.
        verbosity : int
            Verbosity level, lowest is 0. Messages from levels above this
            won't be written to the log..

    Returns:
        ``log.Logger`` instance.
    """

    logdir = logdir or '%s_log' % name

    return Logger(
        fname = '%s__%s.log'
        % (
            name,
            Logger.timestamp().replace(' ', '_').replace(':', '.'),
        ),
        settings = settings,
        verbosity = 0,
        logdir = logdir,
        **kwargs,
    )


class Logger:
    """
    Core logger implementation.

    Bound to one log file but used by many instances of various objects.
    """

    strftime = time.strftime

    def __init__(
        self,
        fname: str,
        settings: 'Settings',
        verbosity: Optional[int] = None,
        console_level: Optional[int] = None,
        logdir: Optional[str] = None,
        max_width: int = 200,
    ):
        """
        Create a new logger.

        Args:
            fname:
                Log file name.
            settings:
                The ``Settings`` instance of the module.
            logdir:
                Path to the directory containing the log files.
            verbosity:
                Messages at and below this level will be written into the
                logfile. All other messages will be dropped.
            console_level:
                Messages below this log level will be printed not only into
                logfile but also to the console.
            max_width:
                Maximum line width (longer lines will be wrapped).
        """

        @_log_flush_timeloop.job(
            interval = datetime.timedelta(
                seconds = settings.get('log_flush_interval'),
            ),
        )
        def _flush():

            self.flush()

        _log_flush_timeloop.start(block = False)

        self.settings = settings
        self.wrapper = textwrap.TextWrapper(
            width = max_width,
            subsequent_indent = ' ' * 22,
            break_long_words = False,
        )
        self.logdir = self.get_logdir(logdir)
        self.fname = os.path.join(self.logdir, fname)
        self.verbosity = (
            verbosity
            if verbosity is not None
            else self.settings.get('log_verbosity')
        )
        self.console_level = (
            console_level
            if console_level is not None
            else self.settings.get('console_verbosity')
        )
        self.open_logfile()

        # sending some greetings
        self.msg('Welcome!')
        self.msg('Logger started, logging into `%s`.' % self.fname)

    def msg(
        self,
        msg: str = '',
        label: Optional[str] = None,
        level: int = 0,
        wrap: bool = True,
    ):
        """
        Writes a message into the log file.

        Args:
            msg:
                Text of the message.
            label:
                A label to be placed before the message in square brackets.
                Typically it points to the code unit emitting the log message,
                e.g. the module or class.
            level:
                The loglevel. Decides if the message will be written or
                dropped.
            wrap:
                Wrap long messages to multiple lines.
        """

        if level <= self.verbosity:

            msg = self.label_message(msg, label = label)
            msg = self.wrapper.fill(msg) if wrap else msg
            msg = self.timestamp_message(msg)
            self.fp.write(msg.encode('utf8', errors = 'replace'))

        if level <= self.console_level:

            self._console(msg)

    def label_message(self, msg, label = None):
        """
        Adds a label in front of the message.
        """

        label = '[%s] ' % label if label else ''

        return f'{label}{msg}'

    def timestamp_message(self, msg):
        """
        Adds a timestamp in front of the message.
        """

        return f'[{self.timestamp()}] {msg}\n'

    def _console(self, msg):

        sys.stdout.write(msg)
        sys.stdout.flush()

    def console(self, msg: str = '', label: Optional[str] = None):
        """
        Prints a message to the console and also to the logfile.

        Args:
            msg:
                Text of the message.
            label:
                A label to be placed before the message in square brackets.
                Typically it points to the code unit emitting the log message,
                e.g. the module or class.
        """

        self.msg(msg = msg, label = label, level = self.console_level)

    @classmethod
    def timestamp(cls):
        """
        Returns a timestamp of the current time.
        """

        return cls.strftime('%Y-%m-%d %H:%M:%S')

    def __del__(self):
        """
        Clean up before destroying this instance.

        Especially, shut down the timeloop and close the logfile.
        """

        if hasattr(_log_flush_timeloop, 'stop'):

            _log_flush_timeloop.stop()

        self.msg('Logger shut down, logfile `%s` closed.' % self.fname)
        self.msg('Bye.')
        self.close_logfile()

    def get_logdir(self, dirname = None):
        """
        Path to the log directory.

        Returns the path to log directory, creates the directory if it does
        not exist.
        """

        dirname = dirname or '%s_log' % self.settings.get('module_name')

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return os.path.abspath(dirname)

    def open_logfile(self):
        """
        Opens the log file.
        """

        self.close_logfile()

        self.fp = open(self.fname, 'wb')

    def close_logfile(self):
        """
        Closes the log file.
        """

        if hasattr(self, 'fp') and not self.fp.closed:

            self.fp.close()

    def flush(self):
        """
        Flushes the log file.
        """

        if hasattr(self, 'fp') and not self.fp.closed:

            self.fp.flush()

    def browse(self):
        """
        Browse the log file.
        """

        with open(self.fname) as fp:

            pydoc.pager(fp.read())

    def __repr__(self):  # noqa: D105

        return 'Logger [%s]' % self.fname

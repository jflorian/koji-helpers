# coding=utf-8

# Copyright 2017-2018 John Florian <jflorian@doubledog.org>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of koji-helpers.
#
# koji-helpers is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version so long as this copyright notice remains intact.
#
# koji-helpers is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# koji-helpers.  If not, see <http://www.gnu.org/licenses/>.

from logging import getLogger

from koji_helpers import CONFIG
from koji_helpers.config import Configuration
from koji_helpers.gojira.monitor import BuildRootDependenciesMonitor

GOJIRA_STATE = '/var/lib/koji-helpers/gojira/state'

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2017-2018 John Florian"""

_log = getLogger(__name__)


class GojiraDaemon(object):
    """
    A pseudo-daemon that spawns one BuildRootDependenciesMonitor for each
    configured buildroot.  Each will monitor one or more of Koji's external
    repositories to determine when it's necessary for Koji to regenerate its
    internal metadata for them thereby keeping the buildroot from becoming
    stale.

    This daemon does not fork, exit, etc. in the classic sense, but does run
    indefinitely performing the task described above.  This operates entirely as
    a single thread and the time intervals mentioned herein should be understood
    to represent a minimum amount of time rather than some precise interval.
    """

    def __init__(self, config_name: str = CONFIG):
        """
        Initialize the GojiraDaemon object.

        :param config_name:
            The name of the configuration file that governs this daemon's
            behavior.
        """
        self.config = Configuration(config_name)
        self.__monitors = []

    def __repr__(self) -> str:
        return ('{}.{}('
                'config_name={!r}, '
                ')').format(
            self.__module__, self.__class__.__name__,
            self.config.filename,
        )

    def __str__(self) -> str:
        return 'Gojira Daemon with {:,d} monitors'.format(
            len(self.__monitors),
        )

    def run(self):
        _log.info('starting an external repo monitor for each buildroot')
        for buildroot in self.config.buildroots:
            deps_monitor = BuildRootDependenciesMonitor(buildroot, self.config)
            self.__monitors.append(deps_monitor)
            deps_monitor.start()
        for monitor in self.__monitors:
            monitor.join()

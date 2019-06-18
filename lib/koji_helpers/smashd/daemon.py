# coding=utf-8

# Copyright 2016-2019 John Florian <jflorian@doubledog.org>
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

import json
from datetime import datetime
from logging import getLogger
from time import sleep

from doubledog.quiescence import QuiescenceMonitor

from koji_helpers import CONFIG
from koji_helpers.config import Configuration
from koji_helpers.smashd.distrepo import DistRepoMaker
from koji_helpers.smashd.notifier import Notifier
from koji_helpers.smashd.signer import Signer
from koji_helpers.smashd.tag_history import KojiTagHistory

SMASHD_STATE = '/var/lib/koji-helpers/smashd/state'

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2019 John Florian"""

_log = getLogger(__name__)


class SignAndComposeDaemon(object):
    """
    A pseudo-daemon that monitors a Koji Hub for events that involve tag
    operations.  When such events are detected, the daemon waits for the
    activity to quiesce for a specified period.  Once quiescence is achieved,
    the daemon will:
        1. sign RPMs for the affected builds
        2. generate new package repositories for the affected tags

    This daemon does not fork, exit, etc. in the classic sense, but does run
    indefinitely performing the task described above.  This operates entirely as
    a single thread and the time intervals mentioned herein should be understood
    to represent a minimum amount of time rather than some precise interval.
    """

    def __init__(self, config_name: str = CONFIG):
        """
        Initialize the SignAndComposeDaemon object.

        :param config_name:
            The name of the configuration file that governs this daemon's
            behavior.
        """
        self.config = Configuration(config_name)
        self._check_interval = self.config.smashd_min_interval
        self._monitor = None
        self.__last_run = None
        self.__mark = None

    def __repr__(self) -> str:
        return (f'{self.__module__}.{self.__class__.__name__}('
                f'config_name={self.config.filename!r}, '
                f')')

    def __str__(self) -> str:
        return f'SignAndComposeDaemon'

    @property
    def last_run(self):
        if self.__last_run is None:
            try:
                with open(SMASHD_STATE) as f:
                    self.__last_run = json.load(f)
                _log.debug(
                    f'loaded last-run of {self.__last_run!r} '
                    f'from {SMASHD_STATE!r}'
                )
            except FileNotFoundError:
                self.__last_run = self.__now_iso_format
                _log.debug(
                    f'initialized last-run to {self.__last_run!r} '
                    f'since {SMASHD_STATE!r} is absent'
                )
        return self.__last_run

    @last_run.setter
    def last_run(self, value):
        self.__last_run = value
        with open(SMASHD_STATE, 'w') as f:
            json.dump(self.__last_run, f)
        _log.debug(f'saved last-run to {self.__last_run!r}')

    @property
    def __now(self):
        # TODO - ideally utcnow() would be used instead
        # Experimentation gives the impression that the koji CLI does not
        # support UTC.
        # See:  https://pagure.io/koji/issue/181
        return datetime.now()

    @property
    def __now_iso_format(self):
        return self.__now.isoformat(sep=' ')

    def __adjust_periods(self, elapsed_time):
        """
        Adjust the quiescent-period to half the length of the last work cycle.

        Statistically, that leaves the probability of delaying this or the
        next cycle equal.  Without any quiescence period, a straggling event
        would have to wait unduly long for present events to be processed.
        A quiescence period that is the full length of the last work cycle
        could mean that present events wait unduly long for a straggler that
        may not be coming.

        The check-interval is adjusted to be one quarter of the
        quiescent-period provided the constraint is not violated.

        Both are constrained to be no less than *min_interval* seconds and no
        more than *max_interval* seconds.

        :param elapsed_time:
            timedelta of the last work cycle.
        """
        last = elapsed_time.total_seconds()
        self._monitor.period = min(
            max(last / 2, self.config.smashd_min_interval),
            self.config.smashd_max_interval
        )
        self._check_interval = min(
            max(self._monitor.period / 4, self.config.smashd_min_interval),
            self.config.smashd_max_interval
        )
        _log.info(
            f'check-interval/quiescent-period adjusted to '
            f'{self._check_interval:0,.1f}/{self._monitor.period:0,.1f} seconds'
        )

    def __get_present_changes(self):
        hist = KojiTagHistory(self.last_run, self.__mark,
                              self.config.smashd_exclude_tags)
        return hist.changed_tags

    def __rest(self):
        _log.debug(f'sleeping {self._check_interval} seconds')
        sleep(self._check_interval)

    def run(self):
        _log.info('started; waiting for tag events')
        changes = {}
        self._monitor = QuiescenceMonitor(self.config.smashd_min_interval,
                                          changes)
        while True:
            self.__mark = self.__now_iso_format
            _log.debug(f'checking for tag events since {self.last_run!r}')
            changes = self.__get_present_changes()
            self._monitor.update(changes)
            if changes:
                _log.debug('new tag events detected')
                if self._monitor.has_quiesced:
                    _log.debug('quiescence achieved')
                    start_time = self.__now
                    Signer(changes, self.config)
                    tags = changes.keys()
                    DistRepoMaker(tags, self.config)
                    elapsed_time = self.__now - start_time
                    self.last_run = self.__mark
                    Notifier(changes, self.config)
                    self.__adjust_periods(elapsed_time)
                else:
                    _log.debug('awaiting quiescence')
            self.__rest()

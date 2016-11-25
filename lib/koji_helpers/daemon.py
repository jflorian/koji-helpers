# coding=utf-8

# Copyright 2016 John Florian <jflorian@doubledog.org>
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

from koji_helpers import CONFIG
from koji_helpers.config import Configuration
from koji_helpers.mash.masher import Masher
from koji_helpers.sign.signer import Signer
from koji_helpers.tag_history import KojiTagHistory

SMASHD_STATE = '/var/lib/koji-helpers/smashd/state'

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016 John Florian"""

_log = getLogger(__name__)


class SignAndMashDaemon(object):
    """
    A pseudo-daemon that monitors a Koji Hub for events that involve tag
    operations.  When such events are detected, the daemon waits for the
    activity to quiesce for a specified period.  Once quiescence is achieved,
    the daemon will:
        1. sign RPMs for the affected builds
        2. mash new temporary package repositories for the affected tags
        3. synchronize the exposed package repositories with the temporary ones

    This daemon does not fork, exit, etc. in the classic sense, but does run
    indefinitely performing the task described above.  This operates entirely as
    a single thread and the time intervals mentioned herein should be understood
    to represent a minimum amount of time rather than some precise interval.
    """

    def __init__(self, config_name: str = CONFIG):
        """
        Initialize the SignAndMashDaemon object.

        :param config_name:
            The name of the configuration file that governs this daemon's
            behavior.
        """
        self.config = Configuration(config_name)
        self.__last_run = None
        self.__mark = None
        self.__quiesce_start = None

    def __repr__(self) -> str:
        return ('{}.{}('
                'config_name={!r}, '
                ')').format(
            self.__module__, self.__class__.__name__,
            self.config.filename,
        )

    def __str__(self) -> str:
        return 'SignAndMashDaemon'.format(
        )

    @property
    def last_run(self):
        if self.__last_run is None:
            try:
                with open(SMASHD_STATE) as f:
                    self.__last_run = json.load(f)
                _log.debug(
                    'loaded last-run of {!r} from {!r}'.format(
                        self.__last_run,
                        SMASHD_STATE,
                    )
                )
            except FileNotFoundError:
                self.__last_run = self.__now_iso_format
                _log.debug(
                    'initialized last-run to {!r} since {!r} is absent'.format(
                        self.__last_run,
                        SMASHD_STATE,
                    )
                )
        return self.__last_run

    @last_run.setter
    def last_run(self, value):
        self.__last_run = value
        with open(SMASHD_STATE, 'w') as f:
            json.dump(self.__last_run, f)
        _log.debug(
            'saved last-run to {!r}'.format(self.__last_run, SMASHD_STATE)
        )

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

    @property
    def __quiescent_elapsed(self):
        period = self.__now - self.__quiesce_start
        return period.total_seconds()

    @property
    def __quiescent_long_enough(self) -> bool:
        return self.__quiescent_elapsed >= self.config.smashd_quiescent_period

    def __get_present_changes(self):
        hist = KojiTagHistory(self.last_run, self.__mark,
                              self.config.smashd_exclude_tags)
        return hist.changed_tags

    def __rest(self):
        period = self.config.smashd_check_interval
        _log.debug('sleeping {} seconds'.format(period))
        sleep(period)

    def __start_quiescent_period(self):
        self.__quiesce_start = self.__now

    def run(self):
        _log.info('started; waiting for tag events')
        prior_changes = {}
        while True:
            self.__mark = self.__now_iso_format
            _log.debug(
                'checking for tag events since {!r}'.format(self.last_run)
            )
            present_changes = self.__get_present_changes()
            if ((present_changes or prior_changes) and
                    (present_changes != prior_changes)):
                prior_changes = present_changes.copy()
                self.__start_quiescent_period()
                _log.debug('new tag events detected; awaiting quiescence')
            elif present_changes:
                if self.__quiescent_long_enough:
                    _log.debug('quiescence achieved')
                    _log.info('signing due to {}'.format(present_changes))
                    Signer(present_changes, self.config)
                    _log.info('mashing due to {}'.format(present_changes))
                    tags = present_changes.keys()
                    Masher(tags, self.config)
                    self.last_run = self.__mark
                    prior_changes = {}
            self.__rest()

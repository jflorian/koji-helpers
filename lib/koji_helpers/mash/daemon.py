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

from doubledog.config.rc import BasicConfigParser

from koji_helpers.mash.masher import Masher
from koji_helpers.tag_history import KojiTagHistory

MASHES_CONF = '/etc/koji-helpers/mashes.conf'
SMASHD_CONF = '/etc/koji-helpers/smashd.conf'
SMASHD_STATE = '/var/lib/koji-helpers/smashd/state'

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016 John Florian"""

_log = getLogger(__name__)


class MashDaemon(object):
    """
    A pseudo-daemon that monitors a Koji Hub for events that involve tag
    operations.  When such events are detected, the daemon waits for the
    activity to quiesce for a specified period.  Once quiescence is achieved,
    the daemon will launch a mash process to compose new package repositories
    for the affected tags.

    This daemon does not fork, exit, etc. in the classic sense, but does run
    indefinitely performing the task described above.  This operates entirely as
    a single thread and the time intervals mentioned herein should be understood
    to represent a minimum amount of time rather than some precise interval.
    """

    def __init__(self,
                 smashd_conf_name: str = SMASHD_CONF,
                 mashes_conf_name: str = MASHES_CONF,
                 check_interval: float = 10,
                 quiescent_period: float = 30,
                 exclude_tags: list = None,
                 ):
        """
        Initialize the MashDaemon object.

        :param smashd_conf_name:
            The name of the configuration file that governs this daemons
            behavior.

        :param mashes_conf_name:
            The name of the configuration file that provides a mapping between
            mash configuration names and file system path names relative to the
            *repo_dir* setting within the *smashd_conf_name*.

        :param check_interval:
            The number of seconds to wait between checks for new tag events.

        :param quiescent_period:
            How many seconds must pass after new tag events are detected without
            any further new tag events being detected before the mash process is
            initiated.

        :param exclude_tags:
            A list of str naming tags that should be excluded from the history.
        """
        self.smashd_config = BasicConfigParser(smashd_conf_name)
        self.mashes_config = BasicConfigParser(mashes_conf_name,
                                               delimit_chars=':')
        self.check_interval = check_interval
        self.quiescent_period = quiescent_period
        self.exclude_tags = exclude_tags or []
        self.__last_run = None
        self.__mark = None
        self.__quiesce_start = None

    def __repr__(self) -> str:
        return ('{}.{}('
                'smashd_conf_name={!r}, '
                'mashes_conf_name={!r}, '
                'check_interval={!r}, '
                'quiescent_period={!r}, '
                'exclude_tags={!r})').format(
            self.__module__, self.__class__.__name__,
            self.smashd_config.filename,
            self.mashes_config.filename,
            self.check_interval,
            self.quiescent_period,
            self.exclude_tags,
        )

    def __str__(self) -> str:
        return 'MashDaemon'.format(
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

    def __get_present_changes(self):
        hist = KojiTagHistory(self.last_run, self.__mark, self.exclude_tags)
        return hist.changed_tags

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
                if self.__quiescent_elapsed >= self.quiescent_period:
                    _log.debug('quiescence achieved')
                    _log.info('mashing due to {}'.format(present_changes))
                    tags = present_changes.keys()
                    Masher(tags, self.smashd_config, self.mashes_config)
                    self.last_run = self.__mark
                    prior_changes = {}
            _log.debug('sleeping {} seconds'.format(self.check_interval))
            sleep(self.check_interval)

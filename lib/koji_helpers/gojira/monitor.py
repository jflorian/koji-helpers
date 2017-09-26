# coding=utf-8

# Copyright 2017 John Florian <jflorian@doubledog.org>
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
import os
from datetime import datetime
from logging import getLogger
from subprocess import CalledProcessError
from threading import Thread
from time import sleep

import requests
from doubledog.quiescence import QuiescenceMonitor

from koji_helpers.config import Configuration
from koji_helpers.koji import KojiRegenRepo, KojiTaskInfo, KojiWaitRepo
from koji_helpers.logging import KojiHelperLoggerAdapter

# This serves as minimum for both the check-interval and quiescence-period.
# Anything less than this gains little and is abusive.
MIN_INTERVAL = 60

GOJIRA_STATE = '/var/lib/koji-helpers/gojira/'

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2017 John Florian"""


class BuildRootDependenciesMonitor(Thread):
    """
    A thread that monitors one or more package repositories that are external
    to Koji and which are dependencies to **one** of its buildroots.  The
    thread will periodically check the metadata for each of the external
    package repositories and upon detecting a change (with adequate
    quiescence), it will trigger Koji into regenerating its internal metadata
    for that buildroot to prevent it from becoming stale.
    """

    def __init__(self, buildroot: str, config: Configuration):
        """
        Initialize the BuildRootDependenciesMonitor object.

        :param buildroot:
            The Koji tag representing one buildroot.

        :param config:
            The :class:`Configuration` instance that governs this monitors's
            behavior.
        """
        super().__init__()
        self.buildroot = buildroot
        self.config = config
        self.name = str(self)
        self._check_interval = MIN_INTERVAL
        self._monitor = None
        self._log = KojiHelperLoggerAdapter(
            getLogger(__name__),
            {'name': str(self)},
        )
        self.__last_metadata = {}
        self.__mark = None

    def __repr__(self) -> str:
        return ('{}.{}('
                'buildroot={!r}, '
                'config={!r}, '
                ')').format(
            self.__module__, self.__class__.__name__,
            self.buildroot,
            self.config,
        )

    def __str__(self) -> str:
        return 'Gojira Monitor for {!r}'.format(
            self.buildroot,
        )

    @property
    def last_metadata(self) -> dict:
        if not self.__last_metadata:
            try:
                with open(self.state_filename) as f:
                    self.__last_metadata = json.load(f)
                self._log.debug(
                    'loaded last-metadata of {!r} from {!r}'.format(
                        self.__last_metadata,
                        self.state_filename,
                    )
                )
            except FileNotFoundError:
                # Assume that an immediate regen is unnecessary.
                self.__last_metadata = self.__get_present_metadata()
                self._log.debug(
                    'initialized last-metadata to {!r} '
                    'since {!r} is absent'.format(
                        self.__last_metadata,
                        self.state_filename,
                    )
                )
        return self.__last_metadata

    @last_metadata.setter
    def last_metadata(self, value: dict):
        # NB: JSON does not support tuples so dump() will cast as list
        self.__last_metadata = value
        with open(self.state_filename, 'w') as f:
            json.dump(self.__last_metadata, f)
        self._log.debug(
            'saved last-metadata to {!r}'.format(
                self.__last_metadata,
                self.state_filename,
            )
        )

    @property
    def state_filename(self) -> str:
        """
        :return:
            The file system path to where this monitor preserves its run-time
            state.
        """
        return os.path.join(GOJIRA_STATE, '{}-state'.format(self.buildroot))

    @property
    def dependency_urls(self) -> iter:
        """
        :return:
            An iter of str with each being one URL referencing an external
            package repository to be monitored.
        """
        br_config = self.config.get_buildroot(self.buildroot)
        for arch in br_config.get('arches').split():
            for dep in br_config.get('dependencies').split():
                url = os.path.join(dep, 'repodata', 'repomd.xml')
                url = url.replace('$basearch', arch)
                yield url

    def __adjust_periods(self, elapsed_time):
        """
        Adjust the quiescent-period to the length of the last work cycle.

        The check-interval is adjusted to be one quarter of the
        quiescent-period provided the constraint is not violated.

        Both are constrained to be no less than MIN_INTERVAL seconds.
        :param elapsed_time:
            timedelta of the last work cycle.
        """
        self._monitor.period = max(MIN_INTERVAL, elapsed_time.total_seconds())
        self._check_interval = max(MIN_INTERVAL, self._monitor.period / 4)
        self._log.info(
            'check-interval/quiescent-period adjusted to '
            '{:0,.1f}/{:0,.1f} seconds'.format(
                self._check_interval,
                self._monitor.period,
            ),
        )

    def __get_present_metadata(self, retries: int = 3, rest: int = 10) -> dict:
        """
        :param retries:
            The maximum number of attempts to be made per each URL before giving
            up.

        :param rest:
            The number of seconds to rest before retrying any failed operation.

        :return:
            A dict whose keys are the URLs of the external package repositories
            being monitored and whose values are a [str, str] list carrying
            the `etag` and `last-modified` values from the HTTP headers for
            that repository's metadata.
        """
        # Unless evidence bears otherwise, we assume that Koji cares about the
        # external repo's metadata *only*.  There's likely to be no info in
        # the rpms themselves not available from the metadata.  Koji may not
        # be able to build with deps from the external repo until quiescence
        # is achieved but that's also true if, in the external repo, the rpms
        # have changed and the metadata hasn't yet caught up.  In other words,
        # we can't guarantee success unless the external repos are updated
        # atomically.
        metadata = {}
        for url in self.dependency_urls:
            self._log.debug('fetching headers for {!r}'.format(url))
            ok = False
            for retry in range(retries):
                if retry:
                    self._log.info(
                        'will retry {}/{} in {} seconds'.format(retry, retries,
                                                                rest)
                    )
                    sleep(rest)
                try:
                    response = requests.head(url)
                except requests.ConnectionError as e:
                    self._log.warning('{}; check your configuration'.format(e))
                else:
                    try:
                        metadata[url] = [
                            response.headers['etag'],
                            response.headers['last-modified'],
                        ]
                    except KeyError as e:
                        self._log.warning(
                            '{} not in HTTP HEAD for {!r}'.format(e, url)
                        )
                    else:
                        if retry:
                            self._log.info('success, at last')
                        ok = True
                        break
            if not ok:
                self._log.error('ignoring this URL for this refresh cycle')
                break
        return metadata

    def __get_changes(self) -> dict:
        """
        Compare the present metadata with prior metadata.

        :return:
            A dict whose keys are one of the external package repositories
            being monitored and whose values are a (str, str) tuple carrying
            the present `etag` and `last-modified` values from the HTTP
            headers for that repository's metadata.  Only those URLs where the
            `etag` and/or `last-modified` values are different from the prior
            metadata are included in the dict.
        """
        changes = {}
        last = self.last_metadata
        for url, data in self.__mark.items():
            if url in last:
                if last[url] != self.__mark[url]:
                    changes[url] = data
            else:
                changes[url] = data
        return changes

    def __regen_repo(self):
        # This won't wait for completion as it would when run from a tty.
        task_id = KojiRegenRepo(self.buildroot).task_id
        self._log.info('newRepo task {!r} started'.format(task_id))
        KojiWaitRepo(self.buildroot)
        state = KojiTaskInfo(task_id).state
        self._log.info('newRepo task {!r} ended as {!r}'.format(task_id, state))

    def __rest(self):
        self._log.debug('sleeping {} seconds'.format(self._check_interval))
        sleep(self._check_interval)

    def run(self):
        """
        Begin monitoring the external repositories for changes.

        Because this class is a `Thread
        <https://docs.python.org/3.5/library/threading.html#thread-objects>`_
        object, this method should not be called directly.  Instead, the
        :method:`start` method should be called.
        """
        self._log.info('started; waiting for changes in external repos')
        # noinspection PyBroadException
        try:
            changes = {}
            self._monitor = QuiescenceMonitor(MIN_INTERVAL, changes)
            while True:
                self._log.debug('checking for changes in external repos')
                self.__mark = self.__get_present_metadata()
                changes = self.__get_changes()
                self._log.debug('present changes are {!r}'.format(changes))
                self._monitor.update(changes)
                if changes:
                    self._log.debug(
                        'external repos changed; awaiting quiescence'
                    )
                    if self._monitor.has_quiesced:
                        self._log.debug('quiescence achieved')
                        self._log.info(
                            'triggering regen due to {}'.format(changes)
                        )
                        try:
                            start_time = datetime.now()
                            self.__regen_repo()
                        except CalledProcessError as e:
                            self._log.error(
                                'regen failed: {}; output was:\n{}'.format(
                                    e,
                                    e.output.decode()
                                )
                            )
                        else:
                            self.last_metadata = self.__mark
                            elapsed_time = datetime.now() - start_time
                            self.__adjust_periods(elapsed_time)
                self.__rest()
        except Exception:
            self._log.exception('died due to unhandled exception')

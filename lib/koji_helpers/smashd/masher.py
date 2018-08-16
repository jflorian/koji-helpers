# coding=utf-8

# Copyright 2016-2018 John Florian <jflorian@doubledog.org>
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
import os
from logging import getLogger
from subprocess import CalledProcessError, STDOUT, check_output
from tempfile import TemporaryDirectory

from koji_helpers import MASH, RSYNC
from koji_helpers.config import Configuration, ConfigurationError, MASH_PATH

RSYNC_ARGS = [RSYNC,
              '--archive',
              '--copy-links',
              '--delay-updates',
              '--delete',
              '--delete-delay',
              '--exclude=lost+found/',
              '--no-group',
              '--no-owner',
              '--stats',
              ]

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2018 John Florian"""

_log = getLogger(__name__)


class Masher(object):
    """
    A wrapper around the mash tool to produce one consumable package repository
    for each Koji build tag passed to the constructor.  All mash work is
    performed in temporary directory.  For each build tag that is successfully
    mashed, the resultant work is then introduced into the publicly consumable
    package repositories for the site.  This happens via the venerable rsync
    tool so as to minimize disruptions to those public repositories.
    """

    def __init__(
            self,
            tags: iter,
            config: Configuration,
    ):
        """
        Initialize the Masher object.
        """
        self.config = config
        self.tags = tags
        self._work = None
        self._tag = None
        self.run()

    def __repr__(self) -> str:
        return ('{}.{}('
                'tags={!r},'
                'config={!r}'
                ')').format(
            self.__module__, self.__class__.__name__,
            self.tags,
            self.config,
        )

    def __str__(self) -> str:
        return 'Masher-{}'.format(self._tag) if self._tag else 'Masher'

    @property
    def _mash_config_name(self) -> str:
        """
        :return:
            The name of the configuration that mash is to be using.
        """
        # We assume a mash configuration exists whose name matches the tag.
        return self._tag

    @property
    def _mash_out_dir(self) -> str:
        """
        :return:
            The file system path to where mash is putting the output.
        """
        # mash output goes into an automatically created subdir
        return os.path.join(self._work, self._tag)

    @property
    def _relative_dir(self) -> str:
        """
        :return:
            The relative file system path where the mash result should land.
        """
        return self.config.get_repo(self._tag)[MASH_PATH]

    @property
    def _repo_dir(self) -> str:
        """
        :return:
            The file system path to the mashed package repositories are to land.
            This value comes from the smashd.conf file.
        """
        return self.config.smashd_repo_dir

    def _mash_tag(self):
        """
        Use the mash tool to extract rpms from Koji for one build tag.

        :return:
            ``True`` iff the mash operation was successful.
        """
        _log.info(
            'mashing into {!r} using config {!r}'.format(
                self._mash_out_dir,
                self._mash_config_name,
            )
        )
        # TODO - eval --previous option as better means for update
        # NB: don't pass self._mash_out_dir here; see comments in that property
        args = [MASH, '-o', self._work, self._mash_config_name]
        _log.debug('about to call {!r}'.format(args))
        try:
            out = check_output(args, stderr=STDOUT)
        except CalledProcessError as e:
            _log.error('{}\noutput:\n{}'.format(e, e.output.decode()))
            return False
        else:
            for line in out.decode().splitlines():
                # Strip mash's log prefix of date, time, argv[0].
                _log.debug('mash: {}'.format(line[26:]))
            return True

    def _sync_repo(self):
        """
        Synchronize the "real" package repo with our just mashed one.

        This actually accomplishes several non-obvious goals::

         - Owner/group attributes can be adjusted to be appropriate for
           exposing which may differ from what mash uses.
         - Disruption to the public area is minimized.  Remember that mash
           itself completely erases a repository and its meta-data before
           rebuilding it.
        """
        # NB: empty dir is to force a trailing slash for correct rsync behavior
        try:
            source = os.path.join(self._mash_out_dir, self._relative_dir, '')
            target = os.path.join(self._repo_dir, self._relative_dir, '')
        except ConfigurationError as e:
            _log.error('cannot sync repo: {}'.format(e))
        else:
            _log.info('synchronizing {!r} with {!r}'.format(target, source))
            args = RSYNC_ARGS + [source, target]
            _log.debug('about to call {!r}'.format(args))
            try:
                out = check_output(args, stderr=STDOUT)
            except CalledProcessError as e:
                _log.error('{}\noutput:\n{}'.format(e, e.output.decode()))
            else:
                for line in out.decode().splitlines():
                    _log.debug('rsync: {}'.format(line))

    def run(self):
        """Mash a package repository for each tag."""
        _log.info('mashing started')
        for self._tag in self.tags:
            with TemporaryDirectory(prefix='{}-'.format(self)) as self._work:
                _log.debug('created work directory {!r}'.format(self._work))
                if self._mash_tag():
                    self._sync_repo()
        _log.info('mashing completed')

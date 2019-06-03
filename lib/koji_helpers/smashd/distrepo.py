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
from logging import getLogger

from koji_helpers.config import Configuration, GPG_KEY_ID
from koji_helpers.koji import KojiDistRepo

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2019 John Florian"""

_log = getLogger(__name__)


class DistRepoMaker(object):
    """
    A wrapper around the Koji's 'dist-repo' feature to compose one consumable
    package repository for each Koji build tag passed to the constructor.  For
    each build tag that is successfully composed there will exist a new
    directory that's created under the `repos-dist` directory of your Koji
    directory (usually `/mnt/koji`).  This new directory will be named as a
    number matching Koji's internal Repo ID.  Once the repository has been
    generated within this new directory, Koji will reestablish a `latest`
    symlink to target it.

    From there, it's a trivial endeavor to bind mount or otherwise serve
    these to the consuming public via HTTP or NFS.
    """

    def __init__(
            self,
            tags: iter,
            config: Configuration,
    ):
        """
        Initialize the DistRepoMaker object.
        """
        self.config = config
        self.tags = tags
        self._work = None
        self._tag = None
        self.run()

    def __repr__(self) -> str:
        return (f'{self.__module__}.{self.__class__.__name__}('
                f'tags={self.tags!r}, '
                f'config={self.config!r}, '
                f')')

    def __str__(self) -> str:
        return f'DistRepoMaker-{self._tag}' if self._tag else 'DistRepoMaker'

    @property
    def _gpg_key_id(self) -> str:
        """
        :return:
            The GPG key identifier by which packages must be signed to be
            allowed into the composed package repository.
        """
        # Koji requires key in lowercase, at least as of Koji 1.17.
        return self.config.get_repo(self._tag)[GPG_KEY_ID].lower()

    @property
    def _repo_config_name(self) -> str:
        """
        :return:
            The name of the smashd configuration section to be used.
        """
        return self._tag

    def run(self):
        """Create/update a package repository for each tag."""
        _log.info('dist-repo creation started')
        for self._tag in self.tags:
            _log.info(
                f'composing dist-repo using config {self._repo_config_name!r}'
            )
            # Task submissions will run async.
            KojiDistRepo(self._tag, self._gpg_key_id)
        _log.info('dist-repo creation completed')

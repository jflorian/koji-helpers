# coding=utf-8

# Copyright 2019 John Florian <jflorian@doubledog.org>
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
import shutil
from datetime import datetime, timedelta
from logging import getLogger

from koji_helpers.config import Configuration
from koji_helpers.koji import SCRATCH

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2019 John Florian"""

_log = getLogger(__name__)


class ScratchBuildCleaner(object):
    """
    A garbage collector for older scratch builds generated by Koji.

    Koji's `build --scratch` feature creates new artifacts that will linger
    forever resulting in ever more cruft accumulating.  This GC will purge
    older artifacts to constrain the amount of cruft that is retained.
    """

    def __init__(
            self,
            config: Configuration,
    ):
        """
        Initialize the ScratchBuildCleaner object.
        """
        self.config = config
        self.run()

    def __repr__(self) -> str:
        return (f'{self.__module__}.{self.__class__.__name__}('
                f'config={self.config!r}, '
                f')')

    def __str__(self) -> str:
        return f'{self.__class__.__name__}'

    def run(self):
        """Purge old scratch builds."""
        if self.config.klean_koji_dir is None:
            raise ValueError('klean/koji_dir is not configured')
        _log.info('scratch-build purge started')
        d = os.path.join(self.config.klean_koji_dir, SCRATCH)
        cutoff = datetime.now() - timedelta(days=90)
        _log.debug(
            f'searching for old scratch-builds under directory {d!r} '
            f'that are older than {cutoff}'
        )
        os.chdir(d)
        users = list(filter(os.path.isdir, os.listdir(d)))
        _log.debug(f'discovered scratch-build tasks for users {users!r}')
        for user in users:
            os.chdir(user)
            tasks = list(filter(os.path.isdir, os.listdir()))
            tasks.sort(key=os.path.getmtime)
            _log.debug(f'discovered for user {user!r} tasks {tasks!r}')
            for task in tasks:
                p = os.path.join(d, user, task)
                if os.path.getmtime(p) < cutoff.timestamp():
                    _log.info(f'purging old scratch-build at {p !r}')
                    shutil.rmtree(p)
                else:
                    _log.info(f'retaining scratch-build at {p !r}')
        _log.info('scratch-build purge completed')

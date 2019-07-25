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

from logging import getLogger

from koji_helpers import CONFIG
from koji_helpers.config import Configuration
from koji_helpers.klean.distrepo import DistRepoCleaner
from koji_helpers.klean.scratchbuild import ScratchBuildCleaner

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2019 John Florian"""

_log = getLogger(__name__)


class KleanTool(object):
    """
    Klean deletes unwanted cruft that Koji produces.

    Cruft is anything that may have once been useful, but has now aged
    sufficiently and thus is doing little more than wasting storage.  This
    includes:
        1. dist-repos
    """

    def __init__(self, config_name: str = CONFIG):
        """
        Initialize the KleanTool object.

        :param config_name:
            The name of the configuration file that governs this daemon's
            behavior.
        """
        self.config = Configuration(config_name)

    def __repr__(self) -> str:
        return (f'{self.__module__}.{self.__class__.__name__}('
                f'config_name={self.config.filename!r}, '
                f')')

    def __str__(self) -> str:
        return f'KleanTool'

    def run(self):
        _log.info('started')
        # Using smashd's repo names as dist tags here.
        DistRepoCleaner(self.config.repos, self.config)
        ScratchBuildCleaner(self.config)
        _log.info('finished')

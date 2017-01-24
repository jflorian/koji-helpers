# coding=utf-8

# Copyright 2016-2017 John Florian <jflorian@doubledog.org>
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

from configparser import ConfigParser
from logging import getLogger

from koji_helpers import CONFIG

# section names
REPOSITORY_PREFIX = 'repository '
SMASHD = 'smashd'

# option names
CHECK_INTERVAL = 'check_interval'
EXCLUDE_TAGS = 'exclude_tags'
GPG_KEY_ID = 'gpg_key_id'
MASH_PATH = 'mash_path'
QUIESCENT_PERIOD = 'quiescent_period'
REPO_DIR = 'repo_dir'
SIGUL_KEY_NAME = 'sigul_key_name'
SIGUL_KEY_PASS = 'sigul_key_pass'

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2017 John Florian"""

_log = getLogger(__name__)


class Configuration(object):
    """
    Configuration for the koji-helpers tools.
    """

    def __init__(self, filename: str = CONFIG):
        """
        Initialize the Configuration object.
        """
        self.filename = filename
        self.__read()

    def __repr__(self) -> str:
        return '{}.{}(filename={!r})'.format(
            self.__module__, self.__class__.__name__,
            self.filename,
        )

    def __str__(self) -> str:
        return 'Configuration({!r})'.format(
            self.filename,
        )

    def __read(self):
        _log.debug('{} reading'.format(self))
        config = ConfigParser()
        config.read(self.filename)
        self.smashd_check_interval = config.getfloat(SMASHD, CHECK_INTERVAL)
        self.smashd_quiescent_period = config.getfloat(SMASHD,
                                                       QUIESCENT_PERIOD)
        self.smashd_exclude_tags = config.get(SMASHD, EXCLUDE_TAGS).split()
        self.smashd_repo_dir = config.get(SMASHD, REPO_DIR)
        self.__repos = {}
        for section in config.sections():
            if section.startswith(REPOSITORY_PREFIX):
                koji_tag = section[len(REPOSITORY_PREFIX):]
                self.__repos[koji_tag] = config[section]
        _log.debug(
            '{} configured {:,d} repos'.format(self, len(list(self.repos)))
        )

    @property
    def repos(self) -> iter:
        """
        :return:
            An iter of str with each being one of the repositories defined in
            the configuration.
        """
        return self.__repos.keys()

    def get_repo(self, name: str):
        """
        :param name:
            The name of the repository configuration to be returned.
        :return:
            The configuration for the named repository.

        """
        return self.__repos[name]

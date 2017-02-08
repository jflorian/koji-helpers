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
import configparser
from logging import getLogger

from koji_helpers import CONFIG

# section names
BUILDROOT_PREFIX = 'buildroot '
GOJIRA = 'gojira'
REPOSITORY_PREFIX = 'repository '
SMASHD = 'smashd'

# option names
CHECK_INTERVAL = 'check_interval'
EXCLUDE_TAGS = 'exclude_tags'
GPG_KEY_ID = 'gpg_key_id'
MASH_PATH = 'mash_path'
NOTIFICATIONS_FROM = 'notifications_from'
NOTIFICATIONS_TO = 'notifications_to'
QUIESCENT_PERIOD = 'quiescent_period'
REPO_DIR = 'repo_dir'
SIGUL_KEY_NAME = 'sigul_key_name'
SIGUL_KEY_PASS = 'sigul_key_pass'

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2017 John Florian"""

_log = getLogger(__name__)


class ConfigurationError(Exception):
    pass


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
        config = configparser.ConfigParser()
        try:
            config.read(self.filename)
            self.smashd_exclude_tags = config.get(SMASHD, EXCLUDE_TAGS).split()
            self.smashd_repo_dir = config.get(SMASHD, REPO_DIR)
            self.smashd_notifications_from = config.get(SMASHD,
                                                        NOTIFICATIONS_FROM)
            self.smashd_notifications_to = config.get(SMASHD,
                                                      NOTIFICATIONS_TO).split()
            self.__buildroots = {}
            self.__repos = {}
            for section in config.sections():
                if section.startswith(BUILDROOT_PREFIX):
                    koji_tag = section[len(BUILDROOT_PREFIX):]
                    self.__buildroots[koji_tag] = config[section]
                elif section.startswith(REPOSITORY_PREFIX):
                    koji_tag = section[len(REPOSITORY_PREFIX):]
                    self.__repos[koji_tag] = config[section]
        except configparser.Error as e:
            raise ConfigurationError(
                'bad configuration: {}'.format(e)
            ) from None

        _log.debug(
            '{} configured {:,d} repos and {:,d} buildroots'.format(
                self,
                len(list(self.repos)),
                len(list(self.buildroots)),
            )
        )

    @property
    def buildroots(self) -> iter:
        """
        :return:
            An iter of str with each being one of the buildroots defined in
            the configuration.
        """
        return self.__buildroots.keys()

    @property
    def repos(self) -> iter:
        """
        :return:
            An iter of str with each being one of the repositories defined in
            the configuration.
        """
        return self.__repos.keys()

    def get_buildroot(self, name: str):
        """
        :param name:
            The name of the buildroot configuration to be returned.
        :return:
            The configuration for the named buildroot.
        """
        try:
            return self.__buildroots[name]
        except KeyError:
            raise ConfigurationError(
                'missing buildroot configuration for {!r}'.format(name)
            ) from None

    def get_repo(self, name: str):
        """
        :param name:
            The name of the repository configuration to be returned.
        :return:
            The configuration for the named repository.
        """
        try:
            return self.__repos[name]
        except KeyError:
            raise ConfigurationError(
                'missing repository configuration for {!r}'.format(name)
            ) from None

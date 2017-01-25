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

import re
from logging import getLogger

from koji_helpers.koji import KojiListHistory

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2017 John Florian"""

# keys
BUILD = 'build'
DIRECTION = 'direction'
TAG_IN = 'in'
TAG_OUT = 'out'
TAG = 'tag'
TIME = 'time'
USER = 'user'

# pre-compiled regex
TAGGED_RE = re.compile(
    '^(?P<{}>.*\d{{4}}) (?P<{}>\S+) (?P<{}>tagged into|untagged from) '
    '(?P<{}>\S+) by (?P<{}>\S+).*$'.format(
        TIME, BUILD, DIRECTION, TAG, USER,
    )
)

_log = getLogger(__name__)


class KojiTagHistory(object):
    """
    A trivial wrapper around "koji list-history" for the purposes of monitoring
    events that involve tag operations.
    """

    def __init__(self, after: str, before: str, exclude_tags: list):
        """
        Initialize the KojiTagHistory object.

        :param after:
            Include only tag history events occurring after this timestamp,
            expressed per RFC 3339 format.

        :param before:
            Include only tag history events occurring before this timestamp,
            expressed per RFC 3339 format.

        :param exclude_tags:
            A list of str naming tags that should be excluded from the history.
        """
        self.after = after
        self.before = before
        self.exclude_tags = exclude_tags

    def __repr__(self) -> str:
        return '{}.{}(after={!r}, before={!r}, exclude_tags={!r})'.format(
            self.__module__, self.__class__.__name__,
            self.after,
            self.before,
            self.exclude_tags,
        )

    @property
    def __koji_history(self):
        return KojiListHistory(self.after, self.before).output.splitlines()

    @property
    def __parsed_history(self) -> list:
        changes = []
        for line in self.__koji_history:
            m = TAGGED_RE.match(line)
            if m:
                m = m.groupdict()
                _log.debug(
                    'tag {!r} affected by build {!r} '
                    'by {!r} request of {!r} at {!r}'.format(
                        m[TAG], m[BUILD], m[DIRECTION], m[USER], m[TIME],
                    )
                )
                changes.append(m)
        return changes

    @property
    def changed_tags(self) -> dict:
        """
        :return:
            A dict structure containing a set of build names or user names
            respectively that triggered the tag history event(s).  The dict
            structure takes the following form:

                TAG:
                    'in':
                        BUILD: set
                        USER: set
                    'out':
                        BUILD: set
                        USER: set
        """
        triggers = {}
        for change in self.__parsed_history:
            assert isinstance(change, dict)
            tag = change[TAG]
            if tag in self.exclude_tags:
                continue
            if tag not in triggers:
                triggers[tag] = {
                    TAG_IN: {BUILD: set(), USER: set()},
                    TAG_OUT: {BUILD: set(), USER: set()},
                }
            direction = TAG_IN if 'into' in change[DIRECTION] else TAG_OUT
            triggers[tag][direction][BUILD].add(change[BUILD])
            triggers[tag][direction][USER].add(change[USER])
        return triggers

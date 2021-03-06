# coding=utf-8

# Copyright 2017-2019 John Florian <jflorian@doubledog.org>
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
import re
from logging import getLogger
from os.path import basename
from subprocess import CalledProcessError, STDOUT, check_output

from koji_helpers import KOJI
from koji_helpers.logging import KojiHelperLoggerAdapter

# The directory name where output of `koji dist-repo` lands.
REPOS_DIST = 'repos-dist'

# The symlink name referencing the latest dist-repo created by `koji dist-repo`.
LATEST = 'latest'

# The directory name where artifacts from `koji build --scratch` land.
SCRATCH = 'scratch'

CREATED_TASK_PATTERN = re.compile(r'Created task: *(\d+)', re.MULTILINE)
STATE_PATTERN = re.compile(r'State: *(\S+)', re.MULTILINE)

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2017-2019 John Florian"""


class KojiCommand(object):
    """
    A wrapper around the Koji Client CLI.

    This exists primarily due to the fact that this project is Python3-based
    while Koji itself remains stuck in Python2.  It also lends a modicum of
    API abstraction which may be beneficial given its deep ties to Koji while
    remaining an external, unassociated project.

    Note that while many of Koji's commands may sport a `--no-wait` option,
    Koji will effectively be asynchronous implicitly when run without an
    attached tty.

    .. attribute:: args

        The Koji CLI command, options and arguments as passed to the
        constructor after normalizing to the `list` type.


    .. attribute:: output

        The captured and decoded output of stdout and stderr (merged).
    """

    def __init__(self, args):
        """
        Initialize the KojiCommand object.
        """
        self.args = args if isinstance(args, list) else [args]
        self._log = KojiHelperLoggerAdapter(
            getLogger(__name__),
            {'name': str(self)},
        )
        self.output = None
        self.run()

    def __repr__(self) -> str:
        return ('{}.{}('
                'args={!r}'
                ')').format(
            self.__module__, self.__class__.__name__,
            self.args,
        )

    def __str__(self) -> str:
        return '<Koji {!r}>'.format(
            self.args,
        )

    def run(self):
        self._log.debug('starting')
        process_args = [KOJI] + self.args
        self._log.debug(f'process_args={process_args!r}')
        try:
            self.output = check_output(process_args, stderr=STDOUT).decode()
        except CalledProcessError as e:
            self.output = e.output.decode()
            self._log.error(
                'terminated abnormally {}'.format(
                    ('and silently' if self.output.strip() == ''
                     else 'and output:\n{}'.format(self.output))
                )
            )
        else:
            self._log.debug(
                'completed {}'.format(
                    ('silently' if self.output.strip() == ''
                     else 'and output:\n{}'.format(self.output))
                )
            )


class KojiBuildInfo(KojiCommand):
    """
    A wrapper around the `koji buildinfo` command.
    """

    def __init__(self, nvr):
        """
        :param nvr:
            A str or list or str with each being one Name-Version-Release value
            to be queried.
        """
        self.nvr = nvr if isinstance(nvr, list) else [nvr]
        super().__init__(['buildinfo'] + self.nvr)

    def __str__(self) -> str:
        return '<Koji BuildInfo {!r}>'.format(
            self.nvr,
        )

    @property
    def rpms(self) -> set:
        """
        :return:
            A set of str, each being one RPM cited in the build info.
            Remember that each Koji build for NEVR results in one NEVR.src.rpm
            and one or more NEVR.ARCH.rpm.
        """
        rpms, ready = set(), False
        for line in self.output.splitlines():
            if ready:
                rpms.add(basename(line.strip()))
            else:
                ready |= line.strip() == 'RPMs:'
        return rpms


class KojiDistRepo(KojiCommand):
    """
    A wrapper around the `koji dist-repo` command.
    """

    def __init__(self, tag: str, key_id: str):
        """
        :param tag:
            Tag for which the distribution repo is to be built.

        :param key_id:
            GPG signing key ID with which RPMs must be signed if they are to
            be included in the repo.
        """
        self.tag = tag
        self.key_id = key_id
        super().__init__(['dist-repo', '--with-src', self.tag, self.key_id])

    def __str__(self) -> str:
        return f'<Koji DistRepo tag={self.tag!r} key_id={self.key_id}>'


class KojiTaskInfo(KojiCommand):
    """
    A wrapper around the `koji taskinfo` command.
    """

    def __init__(self, task_id: str):
        """
        :param task_id:
            The ID of the task to be queried.
        """
        self.task_id = task_id
        super().__init__(['taskinfo', self.task_id])

    def __str__(self) -> str:
        return '<Koji TaskInfo {!r}>'.format(
            self.task_id,
        )

    @property
    def state(self) -> str:
        match = STATE_PATTERN.search(self.output)
        return match.group(1) if match else 'unknown'


class KojiListHistory(KojiCommand):
    """
    A wrapper around the `koji list-history` command.
    """

    def __init__(self, after: str, before: str):
        """
        :param after:
            Include only tag history events occurring after this timestamp,
            expressed per RFC 3339 format.

        :param before:
            Include only tag history events occurring before this timestamp,
            expressed per RFC 3339 format.
        """
        self.before = before
        self.after = after
        super().__init__([
            'list-history',
            '--after={}'.format(self.after),
            '--before={}'.format(self.before),
        ])

    def __str__(self) -> str:
        return '<Koji ListHistory {!r}-{!r}>'.format(
            self.after,
            self.before,
        )


class KojiListSigned(KojiCommand):
    """
    A wrapper around the `koji list-signed` command.
    """

    def __init__(self, tag: str):
        """
        :param tag:
            Only list RPMs within this tag.
        """
        self.tag = tag
        super().__init__([
            'list-signed',
            '--tag={}'.format(self.tag),
        ])

    def __str__(self) -> str:
        return '<Koji ListSigned tag={!r}'.format(
            self.tag,
        )

    @property
    def rpms(self) -> set:
        """
        :return:
            A set of str, each being one signed RPM within the tag.
        """
        rpms = set()
        for line in self.output.splitlines():
            if line.endswith('.rpm'):
                rpms.add(basename(line.strip()))
        return rpms


class KojiRegenRepo(KojiCommand):
    """
    A wrapper around the `koji regen-repo` command.
    """

    def __init__(self, tag: str):
        """
        :param tag:
            The build tag for which regeneration is to occur.
        """
        self.tag = tag
        super().__init__(['regen-repo', self.tag])

    def __str__(self) -> str:
        return '<Koji RegenRepo {!r}>'.format(
            self.tag,
        )

    @property
    def task_id(self) -> str:
        match = CREATED_TASK_PATTERN.search(self.output)
        return match.group(1) if match else 'unknown'


class KojiWaitRepo(KojiCommand):
    """
    A wrapper around the `koji wait-repo` command.
    """

    def __init__(self, tag: str):
        """
        :param tag:
            The build tag for which regeneration is to be awaited.
        """
        self.tag = tag
        super().__init__(['wait-repo', self.tag])

    def __str__(self) -> str:
        return '<Koji WaitRepo {!r}>'.format(
            self.tag,
        )


class KojiWatchTasks(KojiCommand):
    """
    A wrapper around the `koji watch-tasks` command.
    """

    def __init__(self, channel: str = None, user: str = None):
        """
        :param channel:
            Only tasks in this channel.

        :param user:
            Only tasks for this user.
        """
        self.channel = channel
        self.user = user
        args = ['watch-tasks']
        if channel:
            args += ['--channel', channel]
        if user:
            args += ['--user', user]
        super().__init__(args)

    def __str__(self) -> str:
        return (f'<Koji WatchTasks '
                f'in channel {self.channel!r} '
                f'for user {self.user!r} '
                f'>')


class KojiWriteSignedRpm(KojiCommand):
    """
    A wrapper around the `koji write-signed-rpm` command.
    """

    def __init__(self, signature_key: str, nvr):
        """
        :param signature_key:
            The ID of the key that was used for signing.

        :param nvr:
            A str or list or str with each being one Name-Version-Release value
            to be written.
        """
        self.signature_key = signature_key
        self.nvr = nvr if isinstance(nvr, list) else [nvr]
        super().__init__(['write-signed-rpm', self.signature_key] + self.nvr)

    def __str__(self) -> str:
        return '<Koji WriteSignedRPM {!r} :: {!r}>'.format(
            self.signature_key,
            self.nvr,
        )

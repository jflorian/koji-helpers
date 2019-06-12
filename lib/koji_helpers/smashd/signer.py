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
from subprocess import PIPE, Popen, STDOUT

from koji_helpers import SIGUL
from koji_helpers.config import (
    Configuration, GPG_KEY_ID, SIGUL_KEY_NAME, SIGUL_KEY_PASS,
)
from koji_helpers.koji import KojiBuildInfo, KojiListSigned, KojiWriteSignedRpm
from koji_helpers.smashd.tag_history import BUILD, TAG_IN

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2019 John Florian"""

_log = getLogger(__name__)


class Signer(object):
    """
    A wrapper around the Sigul client to facilitate signing of unsigned rpms.
    """

    def __init__(
            self,
            changes: iter,
            config: Configuration,
    ):
        """
        Initialize the Signer object.
        """
        self.changes = changes
        self.config = config
        self._tag = None
        self._builds = None
        self.run()

    def __repr__(self) -> str:
        return (f'{self.__module__}.{self.__class__.__name__}('
                f'changes={self.changes!r}, '
                f'config={self.config!r}, '
                f')')

    def __str__(self) -> str:
        return f'Signer'

    @property
    def _koji_key(self) -> str:
        """
        :return:
            The GPG key ID of the Koji key associated with the tag currently
            being processed.
        """
        # Koji has strict input requirement that the key ID is lowercase.
        return self.config.get_repo(self._tag)[GPG_KEY_ID].lower()

    @property
    def _sigul_key(self) -> str:
        """
        :return:
            The name of the Sigul key associated with the tag currently being
            processed.
        """
        return self.config.get_repo(self._tag)[SIGUL_KEY_NAME]

    @property
    def _sigul_passphrase(self) -> str:
        """
        :return:
            The passphrase for Sigul key associated with the tag currently
            being processed.  This must be the passphrase that the user
            "repomgr" would use to access this key.
        """
        return self.config.get_repo(self._tag)[SIGUL_KEY_PASS]

    def _get_unsigned_rpms(self) -> list:
        """
        :return:
            A list of str, each being one RPM that resulted from the Koji
            build task(s) which is not yet signed.  Remember that:

            - each Koji build for NEVR results in one NEVR.src.rpm and one or
            more NEVR.ARCH.rpm.

            - RPMs may already be signed (and excluded in the returned value)
            because the triggering event may be a move-tag rather than a build
            proper.
        """
        built_rpms = set()
        for build in self._builds:
            _log.debug(f'getting RPMs for build {build!r}')
            built_rpms.update(KojiBuildInfo(build).rpms)
        _log.debug(f'found built RPMs: {built_rpms!r}')
        signed_rpms = KojiListSigned(tag=self._tag).rpms
        _log.debug(f'found signed RPMs: {signed_rpms!r}')
        unsigned_rpms = built_rpms - signed_rpms
        _log.debug(f'giving unsigned RPMs: {unsigned_rpms!r}')
        return list(unsigned_rpms)

    def _sign_builds(self):
        unsigned_rpms = self._get_unsigned_rpms()
        if not unsigned_rpms:
            _log.info(f'no builds for tag {self._tag!r}s need signing')
            return
        _log.info(f'signing builds {unsigned_rpms!r} for tag {self._tag!r}')
        args = [SIGUL, '--batch', 'sign-rpms', '--store-in-koji', '--koji-only',
                self._sigul_key] + unsigned_rpms
        _log.debug(f'about to call {args!r}')
        sigul = Popen(args, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        out, err = sigul.communicate(
            input=f'{self._sigul_passphrase}\0'.encode()
        )
        returncode = sigul.wait()
        if returncode:
            _log.error(
                f'sigul returned {returncode!r} and output:\n{out.decode()}'
            )
        else:
            for line in out.decode().splitlines():
                _log.debug(f'sigul: {line}')
        # It's probably harmless to continue even if Sigul failed.
        _log.info(
            f'writing RPMs for builds {self._builds!r} '
            f'signed with key {self._koji_key!r}'
        )
        KojiWriteSignedRpm(self._koji_key, self._builds)

    def run(self):
        _log.info(f'signing due to {self.changes}')
        for self._tag, change in self.changes.items():
            self._builds = list(change[TAG_IN][BUILD])
            if self._builds:
                self._sign_builds()
        _log.info('signing completed')

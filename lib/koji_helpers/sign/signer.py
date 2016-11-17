# coding=utf-8

# Copyright 2016 John Florian <jflorian@doubledog.org>
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
from os.path import basename
from subprocess import Popen, PIPE, check_output, STDOUT, CalledProcessError

from doubledog.config.rc import BasicConfigParser

from koji_helpers import KOJI, SIGUL
from koji_helpers.tag_history import BUILD

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016 John Florian"""

_log = getLogger(__name__)


class Signer(object):
    """
    A wrapper around the Sigul client to facilitate signing of unsigned rpms.
    """

    def __init__(
            self,
            changes: iter,
            signing_config: BasicConfigParser,
    ):
        """
        Initialize the Signer object.
        """
        self.changes = changes
        self.signing_config = signing_config
        self._tag = None
        self._builds = None
        self.run()

    def __repr__(self) -> str:
        return '{}.{}()'.format(
            'changes={!r},',
            'signing_config={!r},',
            self.__module__, self.__class__.__name__,
            self.changes,
            self.signing_config,
        )

    def __str__(self) -> str:
        return 'Signer'.format(
        )

    @property
    def _koji_key(self) -> str:
        """
        :return:
            The GPG key ID of the Koji key associated with the tag currently
            being processed.
        """
        # Koji has strict input requirement that the key ID is lowercase.
        return self.signing_config.get(self._tag).split()[0].lower()

    @property
    def _koji_rpms(self) -> list:
        """
        :return:
            A list of str, each being one RPM that resulted from the Koji
            build task(s).  Remember that each Koji build NEVR can results in
            one NEVR.src.rpm and one or more NEVR.ARCH.rpm.
        """
        rpms = []
        for build in self._builds:
            _log.debug('getting RPMs for build {!r}'.format(build))
            args = [KOJI, 'buildinfo', build]
            out = check_output(args).decode()
            ready = False
            for line in out.splitlines():
                if ready:
                    rpm = basename(line.strip())
                    _log.debug('got RPM {!r}'.format(rpm))
                    rpms.append(rpm)
                else:
                    ready |= line.startswith('RPMs:')

        return rpms

    @property
    def _sigul_key(self) -> str:
        """
        :return:
            The name of the Sigul key associated with the tag currently being
            processed.
        """
        return self.signing_config.get(self._tag).split()[1]

    @property
    def _sigul_passphrase(self) -> str:
        """
        :return:
            The passphrase for Sigul key associated with the tag currently
            being processed.  This must be the passphrase that the user
            "repomgr" would use to access this key.
        """
        return self.signing_config.get(self._tag).split()[2]

    def _sign_builds(self):
        _log.info(
            'signing builds {!r} for tag {!r}'.format(
                self._builds,
                self._tag,
            )
        )
        args = [SIGUL, '--batch', 'sign-rpms', '--store-in-koji', '--koji-only',
                self._sigul_key] + self._koji_rpms
        _log.debug('about to call {!r}'.format(args))
        sigul = Popen(args, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        out, err = sigul.communicate(
            input='{}\0'.format(self._sigul_passphrase).encode()
        )
        returncode = sigul.wait()
        if returncode:
            _log.error(
                'sigul returned {!r} and output:\n{}'.format(
                    returncode, out.decode(),
                )
            )
            return False
        else:
            for line in out.decode().splitlines():
                _log.debug('sigul: {}'.format(line))
            return True

    def _write_signed_rpms(self):
        _log.info(
            'writing RPMs for builds {!r} signed with key {!r}'.format(
                self._builds,
                self._koji_key,
            )
        )
        args = [KOJI, 'write-signed-rpm', self._koji_key] + self._builds
        _log.debug('about to call {!r}'.format(args))
        try:
            out = check_output(args, stderr=STDOUT)
        except CalledProcessError as e:
            _log.error('{}\noutput:\n{}'.format(e, e.output.decode()))
        else:
            for line in out.decode().splitlines():
                _log.debug('koji: {}'.format(line))

    def run(self):
        for self._tag, change in self.changes.items():
            self._builds = list(change[BUILD])
            if self._sign_builds():
                self._write_signed_rpms()

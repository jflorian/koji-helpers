# coding=utf-8

# Copyright 2017 John Florian <jflorian@doubledog.org>
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

from doubledog.html.documents import StrictXHTMLDocument
from doubledog.html.elements import Body, Heading, Break
from doubledog.mail import MiniMailer

from koji_helpers.config import Configuration
from koji_helpers.smashd.tag_history import BUILD, TAG_IN, TAG_OUT

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2017 John Florian"""

_log = getLogger(__name__)


class Notifier(object):
    """
    A mailer expressly suited for notifying users of recent builds.
    """

    def __init__(
            self,
            changes: iter,
            config: Configuration,
    ):
        """
        Initialize the SignAndMashDaemon object.
        """
        self.changes = changes
        self.config = config
        self.run()

    def __repr__(self) -> str:
        return ('{}.{}('
                'config={!r}, '
                ')').format(
            self.__module__, self.__class__.__name__,
            self.config,
        )

    def __str__(self) -> str:
        return 'Notifier'.format(
        )

    def run(self):
        recipients = self.config.smashd_notifications_to
        _log.info('sending notification to {!r}'.format(recipients))
        body = Body()
        for tag, change in self.changes.items():
            body.append(Heading(2, tag))
            tag_in_builds = change[TAG_IN][BUILD]
            if tag_in_builds:
                body.append(Heading(3, 'arriving'))
                for build in tag_in_builds:
                    body.append(build)
                    body.append(Break())
            tag_out_builds = change[TAG_OUT][BUILD]
            if tag_out_builds:
                body.append(Heading(3, 'departing'))
                for build in tag_out_builds:
                    body.append(build)
                    body.append(Break())
        subject = 'Tag events have affected package repositories'
        doc = StrictXHTMLDocument(body, title=subject)
        MiniMailer().send(
            self.config.smashd_notifications_from,
            recipients,
            subject,
            doc.get_text(),
            doc.get_html(),
        )

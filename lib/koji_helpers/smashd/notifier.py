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

from logging import getLogger

from doubledog.html.documents import StrictXHTMLDocument
from doubledog.html.elements import Body, Heading, Paragraph, Style
from doubledog.mail import MiniMailer

from koji_helpers.config import Configuration
from koji_helpers.smashd.tag_history import BUILD, TAG_IN, TAG_OUT

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2017-2019 John Florian"""

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
        return (f'{self.__module__}.{self.__class__.__name__}('
                f'config={self.config!r},'
                f' )')

    def __str__(self) -> str:
        return f'Notifier'

    def run(self):
        recipients = self.config.smashd_notifications_to
        _log.info(f'sending notification to {recipients!r}')
        body = Body()
        for tag in sorted(self.changes.keys()):
            body.append(Heading(2, tag))
            for dir_, desc, cls in [
                (TAG_IN, 'arriving', 'in'),
                (TAG_OUT, 'departing', 'out')
            ]:
                builds = self.changes[tag][dir_][BUILD]
                if builds:
                    body.append(Heading(3, desc, attributes={'class': cls}))
                    for build in sorted(builds):
                        body.append(Paragraph(build, attributes={'class': cls}))
        subject = 'Tag events have affected package repositories'
        style = Style(
            *(
                'h3.in {color:green;}',
                'h3.out {color:red;}',
                'p.in {color:green; font-family:monospace;}',
                'p.out {color:red; font-family:monospace;}',
            )
        )
        doc = StrictXHTMLDocument(body, title=subject, style=style)
        MiniMailer().send(
            self.config.smashd_notifications_from,
            recipients,
            subject,
            doc.get_text(),
            doc.get_html(),
        )

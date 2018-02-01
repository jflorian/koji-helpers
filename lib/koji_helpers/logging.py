# coding=utf-8

# Copyright 2017-2018 John Florian <jflorian@doubledog.org>
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
from logging import Filter, LoggerAdapter

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2017-2018 John Florian"""


class KojiHelperLoggerAdapter(LoggerAdapter):
    """
    This `LoggerAdapter
    <https://docs.python.org/3/library/logging.html#loggeradapter-objects>`_
    is tailored to the specific needs of the koji_helpers package.  It
    provides additional context where individual object instances may need to
    distinguish themselves from their peers.
    """

    def process(self, msg, kwargs):
        return '{}:  {}'.format(self.extra['name'], msg), kwargs

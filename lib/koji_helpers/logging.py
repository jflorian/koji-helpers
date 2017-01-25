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
from logging import LoggerAdapter, Filter

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2017 John Florian"""


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


class ModuleNameFilter(Filter):
    """
    A simple `logging filter
    <https://docs.python.org/3/library/logging.html#logging.Filter>`_ to exclude
    `LogRecord
    <https://docs.python.org/3/library/logging.html#logging.LogRecord>`_
    instances originating from any of a list of banned Python module names.
    """

    def __init__(self, exclude=None):
        """
        :param exclude:
            A list of str, each of which describes a module path name that is to
            be excluded.
        :return:
            `True` (to allow logging) of the record unless the
            `LogRecord
            <https://docs.python.org/3/library/logging.html#logging.LogRecord>`_
            originated from a module whose path name ends with any of the
            entries in *exclude*.
        """
        super().__init__()
        self.exclude = exclude

    def filter(self, record):
        if self.exclude is not None:
            for module_name in self.exclude:
                if record.pathname.endswith(module_name):
                    return False
        return True

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

import logging.config

import yaml

from koji_helpers import LOGGING_CONFIG
from koji_helpers.smashd.daemon import SignAndComposeDaemon

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2019 John Florian"""


class SmashdCLI(object):
    """
    A basic command-line interface for startup of the SignAndComposeDaemon.
    """

    def __init__(self, ):
        """
        Initialize the SmashdCLI object.
        """
        with open(LOGGING_CONFIG) as f:
            logging.config.dictConfig(yaml.safe_load(f.read()))
        SignAndComposeDaemon().run()

# coding=utf-8

# Copyright 2016-2018 John Florian <jflorian@doubledog.org>
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

__author__ = """John Florian <jflorian@doubledog.org>"""
__copyright__ = """2016-2018 John Florian"""

from distutils.core import setup

setup(
    name='koji_helpers',
    version='',
    packages=[
        'koji_helpers',
        'koji_helpers.gojira',
        'koji_helpers.smashd',
    ],
    package_dir={'': 'lib'},
    require=[
        'doubledog',
        'requests',
        'yaml',
    ],
    scripts=[
        'bin/gojira',
        'bin/smashd',
    ],
    url='',
    license='GPLv3+',
    author='John Florian',
    author_email='jflorian@doubledog.org',
    description='This package provides modules that are used by the tools in '
                'the koji-helpers package.'
)

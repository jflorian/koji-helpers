# This file is part of koji-helpers.
#
# Copyright 2016-2019 John Florian <jflorian@doubledog.org>
# SPDX-License-Identifier: GPL-3.0-or-later

from distutils.core import setup

setup(
    name='koji_helpers',
    version='@@VERSION@@',
    packages=[
        'koji_helpers',
        'koji_helpers.gojira',
        'koji_helpers.klean',
        'koji_helpers.smashd',
    ],
    package_dir={'': 'lib'},
    requires=[
        'doubledog',
        'requests',
        'yaml',
    ],
    scripts=[
        'bin/gojira',
        'bin/klean',
        'bin/smashd',
    ],
    url='https://www.doubledog.org/git/koji-helpers.git',
    license='GPLv3+',
    author='John Florian',
    author_email='jflorian@doubledog.org',
    description='This package provides modules that are used by the tools in '
                'the koji-helpers package.'
)

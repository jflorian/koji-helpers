# coding=utf-8

from distutils.core import setup

setup(
    name='koji_helpers',
    version='',
    packages=[
        'koji_helpers',
        'koji_helpers.mash',
    ],
    package_dir={'': 'lib'},
    url='',
    license='GPLv3+',
    author='John Florian',
    author_email='jflorian@doubledog.org',
    description='This package provides modules that are used by the tools in '
                'the koji-helpers package.'
)

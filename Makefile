# vim: foldmethod=marker
#
# This file is part of koji-tools.
#
# Copyright 2016-2019 John Florian <jflorian@doubledog.org>
# SPDX-License-Identifier: GPL-3.0-or-later

# Standard spec file parsing {{{1

SPECFILE = $(firstword $(wildcard *.spec))

# If there are sub-packages, assume the first is appropriate in forming NVR.
# The dist macro is defined as a null string because it's normal value is
# unwanted in these query results.
queryspec = $(shell rpm --query --queryformat "%{$(1)}\n" \
							--define="dist %{nil}" \
							--specfile $(SPECFILE) \
					| head --lines=1)

NAME := $(call queryspec,NAME)
VERSION := $(call queryspec,VERSION)
RELEASE := $(call queryspec,RELEASE)

# The treeish we'll archive is effectively the Git tag that tito created.
TREEISH := ${NAME}-${VERSION}-${RELEASE}

# Standard targets {{{1

# target: help - Show all callable targets.
.PHONY: help
help:
	@grep -P '^#\s*target:\s*' Makefile | sort

# target: build - Build the package.
.PHONY: build
build: distutils-build

# target: clean - Remove all build and testing artifacts.
.PHONY: clean
clean: clean-doc clean-pyc

# target: dist - Produce a build for distribution.
.PHONY: dist
dist: koji-build

# target: sources - Produce all forms of source distribution.
.PHONY: sources
sources: tarball

# target: tarball - Produce tarball of source distribution.
.PHONY: tarball
tarball:
	git archive \
		--output=${NAME}-${VERSION}.tar.gz \
		--prefix=${NAME}-${VERSION}/ \
		${TREEISH}

# Project specific variables {{{1

PY3_PKG_NAME := koji_helpers
export PYTHONPATH=lib

# Project specific targets {{{1

# target: clean-doc - Remove all documentation build artifacts.
clean-doc:
	@echo Removing all documentation build artifacts...
	rm -rf doc/html/

# target: clean-pyc - Remove all Python bytecode build artifacts.
.PHONY: clean-pyc
clean-pyc:
	@echo Removing all Python bytecode build artifacts...
	find . \
		\( -name '*.pyc' -type f -delete \) , \
		\( -name '__pycache__' -type d -delete \)

# target: distutils-build - Build the Python package using distutils.
.PHONY: distutils-build
distutils-build: embed-version
	@echo Building the Python package...
	python3 lib/${PY3_PKG_NAME}/setup.py build

# target: embed-version - Embed the version into the sources.
.PHONY: embed-version
embed-version:
	@echo Embedding the version into sources...
	sed -i 's/@@VERSION@@/${VERSION}-${RELEASE}/g' lib/${PY3_PKG_NAME}/*.py

# target: koji-build - Submit build RPM task into Koji.
.PHONY: koji-build
koji-build:
	tito release all

# vim: foldmethod=marker

# Standard spec file parsing {{{1

SPECFILE = $(firstword $(wildcard *.spec))

# If there are sub-packages, assume the first is appropriate in forming NVR.
# The dist macro is defined as a null string because it's normal value is
# unwanted in these query results.
queryspec = $(firstword \
				$(shell rpm --query --queryformat "%{$(1)}\n" \
							--define="dist %{nil}" \
							--specfile $(SPECFILE)) \
			)

NAME := $(call queryspec,NAME)
VERSION := $(call queryspec,VERSION)
RELEASE := $(call queryspec,RELEASE)

# The treeish we'll archive is effectively the Git tag that tito created.
TREEISH := ${NAME}-${VERSION}-${RELEASE}

# Standard targets {{{1

# target: help - Show all callable targets.
help:
	@grep -P '^#\s*target:\s*' Makefile | sort

# target: clean - Remove all build and testing artifacts.
clean: clean-doc clean-pyc

# target: dist - Produce a build for distribution.
dist: koji-build

# target: sources - Produce all forms of source distribution.
sources: tarball

# target: tarball - Produce tarball of source distribution.
tarball:
	git archive \
		--output=${NAME}-${VERSION}.tar.gz \
		--prefix=${NAME}-${VERSION}/ \
		${TREEISH}

# Project specific variables {{{1

# Project specific targets {{{1

# target: clean-doc - Remove all documentation build artifacts.
clean-doc:
	@echo Removing all documentation build artifacts...
	rm -rf doc/html/

# target: clean-pyc - Remove all Python bytecode build artifacts.
clean-pyc:
	@echo Removing all Python bytecode build artifacts...
	find . -name '*.pyc' -delete

# target: koji-build - Submit build RPM task into Koji.
koji-build:
	tito release all

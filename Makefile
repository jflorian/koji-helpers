# Extract NVR from the spec while stripping any macros, specifically the
# disttag macro.
name := $(shell awk '/^Name:/{print $$2}' *.spec)
version := $(shell \
	awk '/^Version:/{print gensub(/%{.*?}/, "", "g", $$2)}' *.spec \
	)
release := $(shell \
	awk '/^Release:/{print gensub(/%{.*?}/, "", "g", $$2)}' *.spec \
	)
# The treeish we'll archive is effectively the Git tag that tito created.
treeish := ${name}-${version}-${release}

# Koji's buildSRPMFromSCM method expects a target named "sources" which
# ultimately must ensure that a tarball of the package's sources and its spec
# file are present.  Our practice is to always keep a spec file in the Git
# repository, but we must build the tarball on the fly to resemble an upstream
# published work.
sources:
	git archive \
		--output=${name}-${version}.tar.gz \
		--prefix=${name}-${version}/ \
		${treeish}

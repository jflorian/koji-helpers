specfile = $(firstword $(wildcard *.spec))

# If there are sub-packages, assume the first is appropriate in forming NVR.
# The dist macro is defined as a null string because it's normal value is
# unwanted in these query results.
queryspec = $(firstword \
				$(shell rpm --query --queryformat "%{$(1)}\n" \
							--define="dist %{nil}" \
							--specfile $(specfile)) \
			)

name := $(call queryspec,NAME)
version := $(call queryspec,VERSION)
release := $(call queryspec,RELEASE)

# The treeish we'll archive is effectively the Git tag that tito created.
treeish := ${name}-${version}-${release}

sources: tarball

tarball:
	@git archive \
		--output=${name}-${version}.tar.gz \
		--prefix=${name}-${version}/ \
		${treeish}

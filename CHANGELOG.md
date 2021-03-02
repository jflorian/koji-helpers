<!---
This file is part of koji-helpers.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright 2019-2021 John Florian <jflorian@doubledog.org>
-->
# Change Log

All notable changes to this project will be documented in this file.  This
project adheres to [Semantic Versioning](http://semver.org/).  This file
adheres to [good change log principles](http://keepachangelog.com/).

<!-- Template

## [VERSION] DATE/WIP
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

-->

## [1.1.1] 2021-03-02
### Added
- `klean` now also purges older scratch-builds
### Changed
- `koji_helpers.koji.KojiCommand` now logs (at the DEBUG level) the process args to be executed
### Fixed
- `klean` crashes if the `latest` link is missing for some reason

## [1.1.0] 2019-06-18
### Changed
- quiescence periods for `smashd` and `gojira` to be *half* of the duration of the prior work cycle for improved responsiveness
### Fixed
- `klean.service` is resource greedy

## [1.0.0] 2019-06-12

This and older versions are only documented in the Git commit history.

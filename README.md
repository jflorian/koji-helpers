<!--
This file is part of koji-helpers.
Copyright 2019 John Florian
SPDX-License-Identifier: GPL-3.0-or-later
-->

# koji-helpers

## Overview

This provides three separate tools to supplement a standard Koji deployment.

### gojira

This tool (and service) will automatically cause your Koji deployment to
regenerate its internal repositories for a buildroot tag when it detects that
the related external repositories change.  Thus, what Kojira does only for
Koji's own internal repositories, Gojira does for the external repositories.

### smashd

This tool (and service) will automatically create package repositories that are
ready for use with tools such as yum and dnf.  The builds are sourced from Koji
and build-tags dictate the target package repository through a flexible
mapping.

### klean

This tool (and service) will purge old artifacts that Koji has generated which
would otherwise accumulate unconstrained and waste storage.

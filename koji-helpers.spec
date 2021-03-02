# vim: foldmethod=marker

%global min_py_ver 3.6
%global python_package_name koji_helpers
%global python_setup lib/%{python_package_name}/setup.py
%global repomgr_group repomgr
%global repomgr_user repomgr

Name:           koji-helpers
Version:        1.1.0
Release:        1%{?dist}

# {{{1 package meta-data
Summary:        Supplementary tools to help in a Koji deployment

Group:          Development/Tools
Vendor:         doubledog.org
License:        GPLv3+
URL:            https://www.doubledog.org/git/%{name}.git
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
%{?systemd_requires}
BuildRequires:  systemd

Requires(pre):  shadow-utils

Requires:       koji
Requires:       python%{python3_pkgversion} >= %{min_py_ver}
Requires:       python%{python3_pkgversion}-PyYAML
Requires:       python%{python3_pkgversion}-requests
Requires:       python3-doubledog >= 3.0.0, python3-doubledog < 4.0.0
Requires:       sigul
Requires:       systemd

%description
This package provides tools that supplement the standard Koji packages.
- gojira:
    This tool (and service) will automatically cause your Koji deployment to
    regenerate its internal repositories for a buildroot tag when it detects
    that the related external repositories change.  Thus, what Kojira does
    only for Koji's own internal repositories, Gojira does for the external
    repositories.
- smashd:
    This tool (and service) will automatically create package repositories
    that are ready for use with tools such as yum and dnf.  The builds are
    sourced from Koji and build-tags dictate the target package repository
    through a flexible mapping.
- klean:
    This tool (and service) will purge old artifacts that Koji has generated
    which would otherwise accumulate unconstrained and waste storage.

# {{{1 prep & build
%prep
%setup -q

%build
make build

# {{{1 install
%install
%{__python3} %{python_setup} install -O1 --skip-build --root %{buildroot}

install -Dp -m 0600 etc/config                  %{buildroot}%{_sysconfdir}/%{name}/config
install -Dp -m 0644 etc/logging.yaml            %{buildroot}%{_sysconfdir}/%{name}/logging.yaml
install -Dp -m 0644 lib/systemd/gojira.service  %{buildroot}%{_unitdir}/gojira.service
install -Dp -m 0644 lib/systemd/klean.service  %{buildroot}%{_unitdir}/klean.service
install -Dp -m 0644 lib/systemd/klean.timer  %{buildroot}%{_unitdir}/klean.timer
install -Dp -m 0644 lib/systemd/smashd.service  %{buildroot}%{_unitdir}/smashd.service

install -d -m 0755 %{buildroot}%{_var}/lib/%{name}/gojira
install -d -m 0755 %{buildroot}%{_var}/lib/%{name}/smashd

# {{{1 pre
%pre
getent group %{repomgr_group} >/dev/null || groupadd -r %{repomgr_group}
getent passwd %{repomgr_user} >/dev/null || \
    useradd -r -g %{repomgr_group} -d %{_sysconfdir}/%{name} -s /sbin/nologin \
    -c 'Koji repository manager' %{repomgr_user}
exit 0

# {{{1 post
%post
%systemd_post gojira.service
%systemd_post klean.service
%systemd_post smashd.service

# {{{1 preun
%preun
%systemd_preun gojira.service
%systemd_preun klean.service
%systemd_preun smashd.service

# {{{1 postun
%postun
%systemd_postun_with_restart gojira.service
%systemd_postun_with_restart klean.service
%systemd_postun_with_restart smashd.service

# {{{1 files
%files

%config(noreplace) %{_sysconfdir}/%{name}/logging.yaml

%dir %{python3_sitelib}/%{python_package_name}

%doc doc/AUTHOR doc/COPYING

%license LICENSE

%{_bindir}/gojira
%{_bindir}/klean
%{_bindir}/smashd
%{_unitdir}/gojira.service
%{_unitdir}/klean.service
%{_unitdir}/klean.timer
%{_unitdir}/smashd.service
%{python3_sitelib}/%{python_package_name}/*
%{python3_sitelib}/*egg-info


%defattr(-,%{repomgr_user},%{repomgr_group},-)

%config(noreplace) %{_sysconfdir}/%{name}/config

%{_var}/lib/%{name}/gojira
%{_var}/lib/%{name}/smashd

# {{{1 changelog
%changelog
* Tue Jun 18 2019 John Florian <jflorian@doubledog.org> 1.1.0-1
- Change - improve smashd/gojira responsiveness (jflorian@doubledog.org)
- Bug - klean.service is resource greedy (jflorian@doubledog.org)
- New - initial CHANGELOG.md (jflorian@doubledog.org)
- Drop - [tito] targets for Fedora 28 (jflorian@doubledog.org)
- New - TODO.md for simple task tracking (jflorian@doubledog.org)

* Wed Jun 12 2019 John Florian <jflorian@doubledog.org> 1.0.0-1
- New - klean service/timer units for systemd (jflorian@doubledog.org)
- New - klean tool (jflorian@doubledog.org)
- New - Configuration.smashd_koji_dir setting (jflorian@doubledog.org)
- Drop - Masher class and its dependencies (jflorian@doubledog.org)
- Change - wait for dist-repo task (jflorian@doubledog.org)
- Change - improve completeness of KojiCommand docs (jflorian@doubledog.org)
- Change - use DistRepoMaker instead of Masher (jflorian@doubledog.org)
- Change - transform Masher into DistRepoMaker (in new module)
  (jflorian@doubledog.org)
- New - koji_helpers.koji.KojiDistRepo class (jflorian@doubledog.org)
- New - koji_helpers.smashd.distrepo module (jflorian@doubledog.org)
- Refactor - rename SignAndMashDaemon to SignAndComposeDaemon
  (jflorian@doubledog.org)
- Refactor - use f-string literals instead of format() (jflorian@doubledog.org)
- Bug - regex patterns should be raw-strings (jflorian@doubledog.org)
- Bug - Signer.__repr__() yields garbage (jflorian@doubledog.org)
- Change - [PyCharm] bump SDK to Python 3.7 (jflorian@doubledog.org)
- New - [tito] targets for Fedora 30 (jflorian@doubledog.org)

* Sun Apr 07 2019 John Florian <jflorian@doubledog.org> 0.7.0-3
- Change - [spec] delegate Python build to Makefile (jflorian@doubledog.org)
- Change - [Makefile] clean __pycache__ files too (jflorian@doubledog.org)
- Janitorial - fixup project URLs (jflorian@doubledog.org)
- Bug - [setup] keyword sb 'requires' not 'require' (jflorian@doubledog.org)
- Change - [Makefile] many targets are actually PHONY (jflorian@doubledog.org)
- Janitorial - modernize spec file (jflorian@doubledog.org)
- Change - bump for EPEL moving to Python 3.6 (jflorian@doubledog.org)
- Drop - [tito] targets for Fedora 27 (jflorian@doubledog.org)

* Fri Nov 16 2018 John Florian <jflorian@doubledog.org> 0.7.0-2
- Bug - Fedora 29 requires newer python3-doubledog (jflorian@doubledog.org)
- Drop - [tito] Fedora 26 release targets (jflorian@doubledog.org)
- New - [tito] targets for Fedora 29 (jflorian@doubledog.org)

* Thu Aug 16 2018 John Florian <jflorian@doubledog.org> 0.7.0-1
- Change - let distutils install our scripts (jflorian@doubledog.org)
- New - min_interval/max_interval for smashd in config (jflorian@doubledog.org)
- Refactor - simplify config parsing (jflorian@doubledog.org)
- Refactor - drop unused constants (jflorian@doubledog.org)
- Refactor - drop unused import (jflorian@doubledog.org)
- Janitorial - add SPDX license identifier globally (jflorian@doubledog.org)
- Change - [PyCharm] bump SDK to Python 3.6 (jflorian@doubledog.org)
- New - [PyCharm] encodings configuration (jflorian@doubledog.org)
- [tito] - restructure epel targets (jflorian@doubledog.org)
- Change - [tito] disttag for EL7 (jflorian@doubledog.org)
- New - [tito] targets for Fedora 28 (jflorian@doubledog.org)

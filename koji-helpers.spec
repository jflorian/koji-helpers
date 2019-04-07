# vim: foldmethod=marker

%global min_py_ver 3.6
%global python_package_name koji_helpers
%global python_setup lib/%{python_package_name}/setup.py
%global repomgr_group repomgr
%global repomgr_user repomgr

Name:           koji-helpers
Version:        0.7.0
Release:        2%{?dist}

# {{{1 package meta-data
Summary:        Supplementary tools to help in a Koji deployment

Group:          Development/Tools
Vendor:         doubledog.org
License:        GPLv3+
URL:            http://www.doubledog.org/git/koji-helpers/
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python%{python3_pkgversion}-devel
%{?systemd_requires}
BuildRequires:  systemd

Requires(pre):  shadow-utils

Requires:       koji
Requires:       mash
Requires:       python%{python3_pkgversion} >= %{min_py_ver}
Requires:       python%{python3_pkgversion}-PyYAML
Requires:       python%{python3_pkgversion}-requests
Requires:       python3-doubledog >= 3.0.0, python3-doubledog < 4.0.0
Requires:       repoview
Requires:       rsync
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

# {{{1 prep & build
%prep
%setup -q

%build
%{__python3} %{python_setup} build

# {{{1 install
%install
rm -rf %{buildroot}

%{__python3} %{python_setup} install -O1 --skip-build --root %{buildroot}

install -Dp -m 0600 etc/config                  %{buildroot}%{_sysconfdir}/%{name}/config
install -Dp -m 0644 etc/logging.yaml            %{buildroot}%{_sysconfdir}/%{name}/logging.yaml
install -Dp -m 0644 lib/systemd/gojira.service  %{buildroot}%{_unitdir}/gojira.service
install -Dp -m 0644 lib/systemd/smashd.service  %{buildroot}%{_unitdir}/smashd.service

install -d -m 0755 %{buildroot}%{_var}/lib/%{name}/gojira
install -d -m 0755 %{buildroot}%{_var}/lib/%{name}/smashd

# {{{1 clean
%clean
rm -rf %{buildroot}

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
%systemd_post smashd.service

# {{{1 preun
%preun
%systemd_preun gojira.service
%systemd_preun smashd.service

# {{{1 postun
%postun
%systemd_postun_with_restart gojira.service
%systemd_postun_with_restart smashd.service

# {{{1 files
%files

%config(noreplace) %{_sysconfdir}/%{name}/logging.yaml

%dir %{python3_sitelib}/%{python_package_name}

%doc doc/AUTHOR doc/COPYING

%license LICENSE

%{_bindir}/gojira
%{_bindir}/smashd
%{_unitdir}/gojira.service
%{_unitdir}/smashd.service
%{python3_sitelib}/%{python_package_name}/*
%{python3_sitelib}/*egg-info


%defattr(-,%{repomgr_user},%{repomgr_group},-)

%config(noreplace) %{_sysconfdir}/%{name}/config

%{_var}/lib/%{name}/gojira
%{_var}/lib/%{name}/smashd

# {{{1 changelog
%changelog
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

* Thu Feb 01 2018 John Florian <jflorian@doubledog.org> 0.6.2-1
- Drop - [tito] Fedora 25 release target (jflorian@doubledog.org)
- Change - replace logging filter with simpler setup (jflorian@doubledog.org)
- Bug - smashd misconfig handled poorly (jflorian@doubledog.org)
- New - [tito] targets for Fedora (jflorian@doubledog.org)

* Tue Sep 26 2017 John Florian <jflorian@doubledog.org> 0.6.1-1
- New - [tito] test-all target (jflorian@doubledog.org)
- Bug - [Makefile] queryspec returns partial value (jflorian@doubledog.org)
- New - [Makefile] 'dist' target (jflorian@doubledog.org)
- New - [Makefile] 'clean' target (jflorian@doubledog.org)
- New - [Makefile] vim folding for better organization (jflorian@doubledog.org)
- New - [Makefile] 'help' target (jflorian@doubledog.org)
- Change - [Makefile] don't hide exec of 'git archive' (jflorian@doubledog.org)
- Refactor - [Makefile] rename all vars (jflorian@doubledog.org)
- Bug - [gojira] Thread dies with incomplete metadata (jflorian@doubledog.org)
- Bug - [gojira] Thread exceptions may not be logged (jflorian@doubledog.org)
- Change - give Gorjira threads a meaningful name (jflorian@doubledog.org)
- Change - logging to syslog doesn't capture level (jflorian@doubledog.org)
- Drop - default defattr directive (jflorian@doubledog.org)
- Bug - [smashd] repoview is not updated in public view
  (jflorian@doubledog.org)
- Drop - Dart-specific tito releasers (jflorian@doubledog.org)

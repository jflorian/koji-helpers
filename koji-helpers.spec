# vim: foldmethod=marker

%global min_py_ver 3.6
%global python_package_name koji_helpers
%global python_setup lib/%{python_package_name}/setup.py
%global repomgr_group repomgr
%global repomgr_user repomgr

Name:           koji-helpers
Version:        1.1.1
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
* Tue Mar 02 2021 John Florian <jflorian@doubledog.org> 1.1.1-1
- Drop - unnecessary dependency on repoview (jflorian@doubledog.org)
- Change - [PyCharm] bump SDK to Python 3.8 (jflorian@doubledog.org)
- Drop - [tito] targets for Fedora 31 (jflorian@doubledog.org)
- New - [tito] targets for Fedora 33 (jflorian@doubledog.org)
- Drop - [tito] targets for Fedora 30 (jflorian@doubledog.org)
- New - [tito] targets for Fedora 32 (jflorian@doubledog.org)
- Drop - [tito] targets for Fedora 29 (jflorian@doubledog.org)
- New - [tito] targets for CentOS 8 (jflorian@doubledog.org)
- New - [tito] targets for Fedora 31 (jflorian@doubledog.org)
- Change - minor logging improvements (jflorian@doubledog.org)
- Refactor - eliminate unnecessary param (jflorian@doubledog.org)
- New - klean now also purges scratch builds (jflorian@doubledog.org)
- Refactor - extract LATEST constant (jflorian@doubledog.org)
- Drop - TODO.md (jflorian@doubledog.org)
- New - README.md (jflorian@doubledog.org)
- New - note about KojiCommand implicit async (jflorian@doubledog.org)
- Change - KojiCommand to log process args for debugging
  (jflorian@doubledog.org)
- Bug - klean crashes if the `latest` link is missing (jflorian@doubledog.org)

* Tue Jun 18 2019 John Florian <jflorian@doubledog.org> 1.1.0-1
- Change - improve smashd/gojira responsiveness (jflorian@doubledog.org)
- Bug - klean.service is resource greedy (jflorian@doubledog.org)
- New - initial CHANGELOG.md (jflorian@doubledog.org)
- Drop - [tito] targets for Fedora 28 (jflorian@doubledog.org)
- New - TODO.md for simple task tracking (jflorian@doubledog.org)

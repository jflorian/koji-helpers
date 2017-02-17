# vim: foldmethod=marker

%global python_package_name koji_helpers
%global python_setup lib/%{python_package_name}/setup.py
%global repomgr_group repomgr
%global repomgr_user repomgr

Name:           koji-helpers
Version:        0.6.0
Release:        1%{?dist}

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
Requires:       python%{python3_pkgversion}
Requires:       python%{python3_pkgversion}-PyYAML
Requires:       python3-doubledog >= 2.1.0
Requires:       python34-requests
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
install -Dp -m 0755 bin/gojira                  %{buildroot}%{_bindir}/gojira
install -Dp -m 0755 bin/smashd                  %{buildroot}%{_bindir}/smashd

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
* Wed Feb 08 2017 John Florian <jflorian@doubledog.org> 0.6.0-1
- Bug - [gojira] connection errors are fatal (jflorian@doubledog.org)
- New - better handling of configuration errors (jflorian@doubledog.org)

* Mon Feb 06 2017 John Florian <jflorian@doubledog.org> 0.5.2-1
- New - include LICENSE file (jflorian@doubledog.org)

* Mon Feb 06 2017 John Florian <jflorian@doubledog.org> 0.5.1-1
- New - include LICENSE file (jflorian@doubledog.org)

* Thu Feb 02 2017 John Florian <jflorian@doubledog.org> 0.5.0-1
- Janitorial - global code reformat (jflorian@doubledog.org)
- New - [smashd] colorize mail notifications (jflorian@doubledog.org)
- Change - minor improvements to logged messages (jflorian@doubledog.org)

* Fri Jan 27 2017 John Florian <jflorian@doubledog.org> 0.4.0-1
- New - [gojira] dynamic quiescent-period adjustment (jflorian@doubledog.org)
- New - [smashd] dynamic quiescent-period adjustment (jflorian@doubledog.org)
- Change - [smashd] only sign unsigned RPMs (jflorian@doubledog.org)
- Refactor - intro KojiBuildInfo.rpms property (jflorian@doubledog.org)
- Change - [smashd] sorted notifications, code font (jflorian@doubledog.org)

* Wed Jan 25 2017 John Florian <jflorian@doubledog.org> 0.3.1-1
- Bug - [smashd] don't sign empty build set (jflorian@doubledog.org)

* Wed Jan 25 2017 John Florian <jflorian@doubledog.org> 0.3.0-1
- Change - [gojira] space delimited buildroot configs (jflorian@doubledog.org)
- New - [smashd] send email notifications of affected repos
  (jflorian@doubledog.org)
- Change - [smashd] classify events as tagging in/out (jflorian@doubledog.org)
- New - KojiListHistory class (jflorian@doubledog.org)
- New - KojiWriteSignedRpm class (jflorian@doubledog.org)
- New - KojiBuildInfo class (jflorian@doubledog.org)
- Drop - obsolete regen-repos service, bin, config, etc.
  (jflorian@doubledog.org)
- New - gojira.service for systemd (jflorian@doubledog.org)
- New - gojira executable (jflorian@doubledog.org)
- New - GojiraCLI class (jflorian@doubledog.org)
- New - GojiraDaemon class (jflorian@doubledog.org)
- New - BuildRootDependenciesMonitor class (jflorian@doubledog.org)
- New - koji_helpers.gojira package (jflorian@doubledog.org)
- New - ModuleNameFilter class (jflorian@doubledog.org)
- New - KojiHelperLoggerAdapter class (jflorian@doubledog.org)
- New - KojiCommand class and several sub-classes (jflorian@doubledog.org)
- Change - redo of Makefile (jflorian@doubledog.org)
- Change - [smashd] log more clearly when ops are done (jflorian@doubledog.org)
- Change - [smashd] improve confusing log message (jflorian@doubledog.org)
- Bug - no such logging handler `short` (jflorian@doubledog.org)
- Refactor - remove unused SignAndMashDaemon attribute (jflorian@doubledog.org)
- Janitorial - minor formatting issues (jflorian@doubledog.org)
- Janitorial - update copyrights (jflorian@doubledog.org)
- New - logging configuration via YAML (jflorian@doubledog.org)
- Janitorial - minor reformatting (jflorian@doubledog.org)
- Refactor - move all smashd modules into new package (jflorian@doubledog.org)
- Refactor - leverage QuiescenceMonitor (jflorian@doubledog.org)
- New - Configuration class (jflorian@doubledog.org)
- Refactor - MashDaemon becomes SignAndMashDaemon (jflorian@doubledog.org)
- Change - extend smashd to sign as needed (jflorian@doubledog.org)
- New - Signer class (jflorian@doubledog.org)
- New - koji_helpers.sign Python package (jflorian@doubledog.org)
- Bug - mislabeled VIM folding section in spec (jflorian@doubledog.org)
- Change - smashd obsoletes mash-everything (jflorian@doubledog.org)
- New - smashd executable -- WIP (jflorian@doubledog.org)
- New - Masher class (jflorian@doubledog.org)
- New - MashDaemon class (jflorian@doubledog.org)
- New - koji_helpers.mash Python package (jflorian@doubledog.org)
- New - KojiTagHistory class (jflorian@doubledog.org)
- New - koji_helpers Python package (jflorian@doubledog.org)
- New - PyCharm deployment configuration (jflorian@doubledog.org)
- New - PyCharm project configuration (jflorian@doubledog.org)

* Wed Aug 31 2016 John Florian <jflorian@doubledog.org> 0.2.0-1
- New - mash-everything tool/service (jflorian@doubledog.org)
- Bug - inaccurate comment (jflorian@doubledog.org)
- Change - regen-repos checksum_of() implementation (jflorian@doubledog.org)
- Bug - regen-repos saving state in wrong directory (jflorian@doubledog.org)
- Change - logging priority levels to be more appropriate
  (jflorian@doubledog.org)
- Change - resolve a number of shellcheck warnings (jflorian@doubledog.org)

* Mon Aug 29 2016 John Florian <jflorian@doubledog.org> 0.1.0-2
- Bug - missing Makefile for KojiGitReleaser (jflorian@doubledog.org)

* Mon Aug 29 2016 John Florian <jflorian@doubledog.org> 0.1.0-1
- new package built with tito

* Mon Aug 29 2016 John Florian <jflorian@doubledog.org>
- new package built with tito


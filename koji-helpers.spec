# vim: foldmethod=marker

%global python_package_name koji_helpers
%global python_setup lib/%{python_package_name}/setup.py
%global repomgr_group repomgr
%global repomgr_user repomgr

Name:           koji-helpers
Version:        0.2.0
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

Requires:       bash
Requires:       coreutils
Requires:       findutils
Requires:       grep
Requires:       koji
Requires:       mash
Requires:       python%{python3_pkgversion}
Requires:       repoview
Requires:       rsync
Requires:       sed

%description
This package provides tools that supplement the standard Koji packages.
- mash-everything:
    This tool (and service) will automatically create package repositories
    that are ready for use with tools such as yum and dnf.  The builds are
    sourced from Koji and build-tags dictate the target package repository
    through a flexible mapping.
- regen-repos: 
    This tool (and service) will automatically cause your Koji deployment to
    regenerate Koji's internal repositories when it detects that your external
    repositories change.  Normally Koji (Kojira actually) only monitors it's
    own internal repositories.

# {{{1 prep & build
%prep
%setup -q

%build
%{__python3} %{python_setup} build

# {{{1 install
%install
rm -rf %{buildroot}

%{__python3} %{python_setup} install -O1 --skip-build --root %{buildroot}

install -Dp -m 0644 etc/mash-everything.conf            %{buildroot}%{_sysconfdir}/%{name}/mash-everything.conf
install -Dp -m 0644 etc/mashes.conf                     %{buildroot}%{_sysconfdir}/%{name}/mashes.conf
install -Dp -m 0644 etc/regen-repos.conf                %{buildroot}%{_sysconfdir}/%{name}/regen-repos.conf
install -Dp -m 0644 etc/repos.conf                      %{buildroot}%{_sysconfdir}/%{name}/repos.conf
install -Dp -m 0644 lib/systemd/mash-everything.service %{buildroot}%{_unitdir}/mash-everything.service
install -Dp -m 0644 lib/systemd/regen-repos.service     %{buildroot}%{_unitdir}/regen-repos.service
install -Dp -m 0755 bin/mash-everything                 %{buildroot}%{_bindir}/mash-everything
install -Dp -m 0755 bin/regen-repos                     %{buildroot}%{_bindir}/regen-repos
install -Dp -m 0755 libexec/_shared                     %{buildroot}%{_libexecdir}/%{name}/_shared

install -d -m 0755 %{buildroot}%{_var}/lib/%{name}/regen-repos
install -d -m 0755 %{buildroot}%{_var}/lib/%{name}/smashd

# {{{1 clean
%clean
rm -rf %{buildroot}

# {{{1 clean
%pre
getent group %{repomgr_group} >/dev/null || groupadd -r %{repomgr_group}
getent passwd %{repomgr_user} >/dev/null || \
    useradd -r -g %{repomgr_group} -d %{_sysconfdir}/%{name} -s /sbin/nologin \
    -c 'Koji repository manager' %{repomgr_user}
exit 0

# {{{1 post
%post
%systemd_post mash-everything.service
%systemd_post regen-repos.service

# {{{1 preun
%preun
%systemd_preun mash-everything.service
%systemd_preun regen-repos.service

# {{{1 postun
%postun
%systemd_postun_with_restart mash-everything.service
%systemd_postun_with_restart regen-repos.service

# {{{1 files
%files
%defattr(-,root,root,-)

%config(noreplace) %{_sysconfdir}/%{name}/mash-everything.conf
%config(noreplace) %{_sysconfdir}/%{name}/mashes.conf
%config(noreplace) %{_sysconfdir}/%{name}/regen-repos.conf
%config(noreplace) %{_sysconfdir}/%{name}/repos.conf

%dir %{python3_sitelib}/%{python_package_name}

%doc doc/AUTHOR doc/COPYING
%{_bindir}/mash-everything
%{_bindir}/regen-repos
%{_libexecdir}/%{name}/_shared
%{_unitdir}/mash-everything.service
%{_unitdir}/regen-repos.service
%{python3_sitelib}/%{python_package_name}/*
%{python3_sitelib}/*egg-info


%defattr(-,%{repomgr_user},%{repomgr_group},-)

%{_var}/lib/%{name}/regen-repos
%{_var}/lib/%{name}/smashd

# {{{1 changelog
%changelog
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


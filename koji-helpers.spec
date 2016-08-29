# vim: foldmethod=marker

%global repomgr_user repomgr
%global repomgr_group repomgr

Name:           koji-helpers
Version:        0.1.0
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

%{?systemd_requires}
BuildRequires:  systemd

Requires(pre):  shadow-utils

Requires:       bash
Requires:       coreutils
Requires:       findutils
Requires:       grep
Requires:       koji

%description
This package provides tools that supplement the standard Koji packages.
- regen-repos: 
    This tool (and service) will automatically cause your Koji deployment to
    regenerate Koji's internal repositories when it detects that your external
    repositories change.  Normally Koji (Kojira actually) only monitors it's
    own internal repositories.

# {{{1 prep & build
%prep
%setup -q

%build

# {{{1 install
%install
rm -rf %{buildroot}

install -Dp -m 0644 etc/regen-repos.conf            %{buildroot}%{_sysconfdir}/%{name}/regen-repos.conf
install -Dp -m 0644 etc/repos.conf                  %{buildroot}%{_sysconfdir}/%{name}/repos.conf
install -Dp -m 0644 lib/systemd/regen-repos.service %{buildroot}%{_unitdir}/regen-repos.service
install -Dp -m 0755 bin/regen-repos                 %{buildroot}%{_bindir}/regen-repos
install -Dp -m 0755 libexec/_shared                 %{buildroot}%{_libexecdir}/%{name}/_shared

install -d -m 0755 %{buildroot}%{_var}/lib/%{name}

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
%systemd_post regen-repos.service

# {{{1 preun
%preun
%systemd_preun regen-repos.service

# {{{1 postun
%postun
%systemd_postun_with_restart regen-repos.service

# {{{1 files
%files
%defattr(-,root,root,-)

%config(noreplace) %{_sysconfdir}/%{name}/regen-repos.conf
%config(noreplace) %{_sysconfdir}/%{name}/repos.conf
%doc doc/AUTHOR doc/COPYING
%{_bindir}/regen-repos
%{_libexecdir}/%{name}/_shared
%{_unitdir}/regen-repos.service

%defattr(-,%{repomgr_user},%{repomgr_group},-)

%{_var}/lib/%{name}

# {{{1 changelog
%changelog
* Mon Aug 29 2016 John Florian <jflorian@doubledog.org> 0.1.0-2
- Bug - missing Makefile for KojiGitReleaser (jflorian@doubledog.org)

* Mon Aug 29 2016 John Florian <jflorian@doubledog.org> 0.1.0-1
- new package built with tito

* Mon Aug 29 2016 John Florian <jflorian@doubledog.org>
- new package built with tito


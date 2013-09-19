
Name: vc-out-parser
Summary: it prases vc-out.xml used by pragma boot https://github.com/pragmagrid/pragma_boot
Version: 1.0
Release: 1
Copyright: GPL
Group: Applications
URL: https://github.com/pragmagrid/vc-out-parser
Vendor: UCSD
Packager: Luca Clementi <luca.clementi@gmail.com>
Source0: vc-out-parser.py
Source1: vc-out-parser


%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}/etc/rc.d/init.d/
cp -p %{SOURCE1} %{buildroot}%{_bindir}/etc/rc.d/init.d/
mkdir -p %{buildroot}%{_bindir}/opt/vc-out-parse
cp -p %{SOURCE1} %{buildroot}%{_bindir}/opt/vc-out-parse



%files
%{_bindir}/etc/rc.d/init.d/*
%{_bindir}/opt/vc-out-parse

%clean
rm -rf %{buildroot}


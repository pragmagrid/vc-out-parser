
Name: vc-out-parser
Summary: It prases vc-out.xml
Version: 1.0
Release: 1
License: GPL
Group: Applications
URL: https://github.com/pragmagrid/vc-out-parser
Vendor: UCSD
Packager: Luca Clementi <luca.clementi@gmail.com>
Source0: vc-out-parser.py
Source1: vc-out-parser

%description
This rpm parses vc-out.xml for pragma boot


%prep

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/etc/rc.d/init.d/
cp -p %{SOURCE1} %{buildroot}/etc/rc.d/init.d/
mkdir -p %{buildroot}/opt/vc-out-parse
cp -p %{SOURCE0} %{buildroot}/opt/vc-out-parse



%files
/etc/rc.d/init.d/*
/opt/vc-out-parse/*

%clean
rm -rf %{buildroot}

%post
/sbin/chkconfig vc-out-parser on

%preun
/sbin/chkconfig vc-out-parser off


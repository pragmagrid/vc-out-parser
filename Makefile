#
# Makefile to build rpm
#

file0 = vc-out-parser.py
file1 = vc-out-parser
sources_folder = ~/rpmbuild/SOURCES/

all: default

default:
	mkdir -p $(sources_folder)
	cp $(file0) $(sources_folder)
	cp $(file1) $(sources_folder)
	rpmbuild -ba vc-out-parser.spec



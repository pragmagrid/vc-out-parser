#!/usr/bin/python
#
# @Copyright@
# 
# 				Rocks(r)
# 		         www.rocksclusters.org
# 		         version 5.6 (Emerald Boa)
# 		         version 6.1 (Emerald Boa)
# 
# Copyright (c) 2000 - 2013 The Regents of the University of California.
# All rights reserved.	
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice unmodified and in its entirety, this list of conditions and the
# following disclaimer in the documentation and/or other materials provided 
# with the distribution.
# 
# 3. All advertising and press materials, printed or electronic, mentioning
# features or use of this software must display the following acknowledgement: 
# 
# 	"This product includes software developed by the Rocks(r)
# 	Cluster Group at the San Diego Supercomputer Center at the
# 	University of California, San Diego and its contributors."
# 
# 4. Except as permitted for the purposes of acknowledgment in paragraph 3,
# neither the name or logo of this software nor the names of its
# authors may be used to endorse or promote products derived from this
# software without specific prior written permission.  The name of the
# software includes the following terms, and any derivatives thereof:
# "Rocks", "Rocks Clusters", and "Avalanche Installer".  For licensing of 
# the associated name, interested parties should contact Technology 
# Transfer & Intellectual Property Services, University of California, 
# San Diego, 9500 Gilman Drive, Mail Code 0910, La Jolla, CA 92093-0910, 
# Ph: (858) 534-5815, FAX: (858) 534-7345, E-MAIL:invent@ucsd.edu
# 
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# @Copyright@
#

import string
import os.path
import os
import xml.etree.ElementTree
import sys


def parse():
	"""
	create configuration files to use the net network configuration specified in 
	the first arguments (the file must be in the format specified in the README file 
	available at
	https://github.com/pragmagrid/pragma_boot/tree/master

	example:  vc-out-parse.py /root/vc-out.xml'>
	"""

	if len(sys.argv) != 2 :
		print('You need to pass the vc-out.xml file as input')
		sys.exit(1)

	vc_out_file = sys.argv[1]
	if not os.path.isfile(vc_out_file):
		print('The %s path does not point to a valid file' % vc_out_file)
		sys.exit(1)

	# get new config values
	vc_out_xmlroot = xml.etree.ElementTree.parse(vc_out_file).getroot()

	# authorize ssh key
	ssh_key = vc_out_xmlroot.findall('./key')
	if ssh_key :
		print "Authorizing ssh key"
		f = open('/root/.ssh/authorized_keys', 'a')
		f.write(ssh_key[0].text.strip() + '\n')
		f.close()

	# write resolve.conf
	dns_node = vc_out_xmlroot.findall('./network/dns')[0]
	dns_servers = dns_node.attrib["ip"]
	static_str = 'search local\n'
	for i in dns_servers.split(','):
		static_str += 'nameserver %s\n' % i
	write_file('/etc/resolv.conf', static_str)

	if len(  vc_out_xmlroot.findall('./compute/private') ) > 0 :
		print "Fixing compute node"
		fixCompute(vc_out_xmlroot)
	else:
		print "Fixing frontend"
		fixFrontend(vc_out_xmlroot)



def fixCompute(vc_out_xmlroot):
	"""fix a compute node network based on the vc-out.xml"""
	xml_node = vc_out_xmlroot.findall('./compute/private')[0]
	private_ip = xml_node.attrib["ip"]
	fqdn = xml_node.attrib["fqdn"]
	netmask = xml_node.attrib["netmask"]
	gw = xml_node.attrib["gw"]
	fe_fqdn = vc_out_xmlroot.findall('./frontend/public')[0].attrib["fqdn"]

	# write ifcfg eth0
	mac = None
	if 'mac' in xml_node.attrib:
		mac = xml_node.attrib["mac"]
	write_ifcfg('eth0', private_ip, netmask, mac)

	# write syconfig/network
	write_file('/etc/sysconfig/network',
		'NETWORKING=yes\nHOSTNAME=%s.local\nGATEWAY=%s\n' % (fqdn, gw))

	# write /etc/hosts
	hosts_str = '127.0.0.1\tlocalhost.localdomain localhost\n'
	hosts_str += '%s\t%s.local %s\n' % (private_ip, fqdn, fqdn)
	hosts_str += '%s\t%s %s\n' % (gw, fe_fqdn, fe_fqdn.split('.')[0])
	write_file('/etc/hosts', hosts_str)

def fixFrontend(vc_out_xmlroot):
	"""fix a frontend based on the vc-out.xml file"""

	# public interface
	pubblic_node = vc_out_xmlroot.findall('./frontend/public')[0]
	public_ip = pubblic_node.attrib["ip"]
	fqdn = pubblic_node.attrib["fqdn"]
	public_netmask = pubblic_node.attrib["netmask"]
	gw = pubblic_node.attrib["gw"]
	public_mac = None
	if 'mac' in pubblic_node.attrib:
		public_mac = pubblic_node.attrib["mac"]
	hostname = fqdn.split('.')[0]

	# private interface
	private_node = vc_out_xmlroot.findall('./frontend/private')[0]
	private_ip = private_node.attrib["ip"]
	private_netmask = private_node.attrib["netmask"]
	private_mac = None
	if 'mac' in private_node.attrib:
		private_mac = private_node.attrib["mac"]

	# write private interface eth0
	write_ifcfg('eth0', private_ip, private_netmask, private_mac)

	# write public interface eth1
	write_ifcfg('eth1', public_ip, public_netmask, public_mac)

	# write syconfig/network
	write_file('/etc/sysconfig/network',
		'NETWORKING=yes\nHOSTNAME=%s\nGATEWAY=%s\n' % (fqdn, gw))

	# write /etc/hosts and /tmp/machine
	hosts_str = '127.0.0.1\tlocalhost.localdomain localhost\n'
	hosts_str += '%s\t%s.local %s\n' % (private_ip, hostname, hostname)
	hosts_str += '%s\t%s\n' % (public_ip, fqdn)
	machine_str = ""

	# adding compute node to the DB
	xml_nodes = vc_out_xmlroot.findall('./compute/node')
	if xml_nodes:
		# add the nodes to the hosts file
		for node_xml in xml_nodes:
			hostname = node_xml.attrib["name"]
			ip = node_xml.attrib["ip"]
			hosts_str +=  '%s\t%s.local %s\n' % (ip, hostname, hostname)
			if 'cpus' in node_xml.attrib:
				cpus = int(node_xml.attrib['cpus'])
				machine_str += ''.join([hostname + '\n' for i in range(0, cpus)])
			else:
				#we can just assume cpu = 1
				machine_str += hostname + '\n'

	write_file('/etc/hosts', hosts_str)
	write_file('/tmp/machinefile', machine_str)



def write_ifcfg(ifname, ip, netmask, mac):
	""" write a ifcfg file with given arguments """
	#TODO deal with MTU
	ifup_str = 'DEVICE=%s\nIPADDR=%s\nNETMASK=%s\n' % (ifname, ip, netmask)
	ifup_str += 'BOOTPROTO=none\nONBOOT=yes\nMTU=1500\n'
	if mac:
		ifup_str += 'HWADDR=%s\n' % mac
	write_file('/etc/sysconfig/network-scripts/ifcfg-%s' % ifname, ifup_str)


def write_file(file_name, content):
	"""write the content in the file_name"""
	f = open(file_name, 'w')
	f.write(content)
	f.close()


if __name__ == "__main__":
    parse()

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
import platform
import subprocess
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
	print "Writing SSH key"
	ssh_key = vc_out_xmlroot.findall('./key')
	if ssh_key :
		print "Authorizing ssh key"
		if not os.path.exists('/root/.ssh'):
			os.mkdir('/root/.ssh')
		f = open('/root/.ssh/authorized_keys', 'a')
		f.write(ssh_key[0].text.strip() + '\n')
		f.close()

	# write resolve.conf
	print "Writing /etc/resolv.conf"
	dns_node = vc_out_xmlroot.find('./network/dns')
	dns_servers = dns_node.attrib["ip"]
	static_str = 'search local\n'
	for i in dns_servers.split(','):
		static_str += 'nameserver %s\n' % i
	write_file('/etc/resolv.conf', static_str)

	hostname = None
	if len(  vc_out_xmlroot.findall('./compute/private') ) > 0 :
		print "Fixing compute node"
		hostname = fixCompute(vc_out_xmlroot)
	else:
		print "Fixing frontend"
		hostname = fixFrontend(vc_out_xmlroot)

	print "Setting hostname"
	subprocess.call('hostname %s' % hostname, shell=True)
	if os.path.exists("/etc/hostname"):
		write_file('/etc/hostname', "%s\n" % hostname)

	print "Done vc-out-parser"



def fixCompute(vc_out_xmlroot):
	"""fix a compute node network based on the vc-out.xml"""
	compute = vc_out_xmlroot.find('./compute')
	(name, gw, fe_fqdn) = (None, None, None)
	try:
		name = compute.attrib["name"]
		gw = compute.attrib["gw"]
		fe_fqdn = vc_out_xmlroot.find('./frontend').attrib["fqdn"]
	except:
		name = compute.find("private").attrib["fqdn"]
		gw = compute.find("private").attrib["gw"]
		fe_fqdn = vc_out_xmlroot.find('./frontend/public').attrib["fqdn"]

	if os.path.exists("/etc/sysconfig/network"):
		write_file('/etc/sysconfig/network',
			'NETWORKING=yes\nHOSTNAME=%s.local\n' % name)

	hosts_str = configure_interfaces_and_hosts(compute, name, None, gw, "private")

	# write /etc/hosts
	print "Writing /etc/hosts"
	hosts_str += '%s\t%s %s\n' % (gw, fe_fqdn, fe_fqdn.split('.')[0])
	write_file('/etc/hosts', hosts_str)

	return '%s.local' % name


def fixFrontend(vc_out_xmlroot):
	"""fix a frontend based on the vc-out.xml file"""

	frontend = vc_out_xmlroot.find('./frontend')
	(fqdn, gw, name) = (None, None, None)
	try:
		fqdn = frontend.attrib["fqdn"]
		gw = frontend.attrib["gw"]
		name = frontend.attrib["name"]
	except: # is old version
		fqdn = frontend.find("public").attrib["fqdn"]
		gw = frontend.find("public").attrib["gw"]
		name = frontend.find("public").attrib["name"]
	if os.path.exists("/etc/sysconfig/network"):
		write_file('/etc/sysconfig/network',
		           'NETWORKING=yes\nHOSTNAME=%s\nGATEWAY=%s\n' % (fqdn,gw))

	hosts_str = configure_interfaces_and_hosts(frontend, name, fqdn, gw, "public")

	machine_str = ""
	# adding compute node to the DB
	xml_nodes = vc_out_xmlroot.findall('./compute/node')
	if xml_nodes:
		# add the nodes to the hosts file
		for node in xml_nodes:
			name = node.attrib["name"]
			if len(list(node)) > 0:
				for iface in node:
					hosts_str = append_host(name, None, iface, hosts_str)
			else: # backwards compatible with old vc-out.xml format
				ip = node.attrib["ip"]
				hosts_str += '%s\t%s.local %s\n' % (ip, name, name)
			if 'cpus' in node.attrib:
				cpus = int(node.attrib['cpus'])
				machine_str += ''.join([name + '\n' for i in range(0, cpus)])
			else:
				#we can just assume cpu = 1
				machine_str += name + '\n'

	# write /etc/hosts and /tmp/machine
	print "Writing /etc/hosts"
	write_file('/etc/hosts', hosts_str)
	print "Writing /tmp/machinefile"
	write_file('/tmp/machinefile', machine_str)

	return fqdn

def configure_interfaces_and_hosts(node, name, fqdn, gw, gw_iface):
	interface_spec = {}
	hosts_str = '127.0.0.1\tlocalhost.localdomain localhost\n'
	for interface in node:
		ip = interface.attrib["ip"]
		netmask = interface.attrib["netmask"]
		mac = interface.attrib["mac"]
		mtu = "1500"
		if "mtu" in interface.attrib:
			mtu = interface.attrib["mtu"]
		iface = get_iface(mac)
		if iface is None:
			print "Unable to find interface for mac %s" % mac
			continue
		print "Configuring iface %s for %s" % (iface, mac)
		iface_gw = None
		interface_spec[iface] = {'ip': ip, 'netmask': netmask, 'mtu': mtu}
		if interface.tag == gw_iface:
			interface_spec[iface]['gw'] = gw
			iface_gw = gw

		# append /etc/hosts
		hosts_str = append_host(name, fqdn, interface, hosts_str)

		# write syconfig/network
		if os.path.exists("/etc/sysconfig/network-scripts"):
			write_ifcfg(iface, ip, netmask, mac, mtu, iface_gw)

	if os.path.exists("/etc/network/interfaces"):
		write_interfaces(interface_spec)

	return hosts_str

def get_iface(mac):
	try:
		p = subprocess.Popen("ip -o link show| grep %s" % mac, shell=True,
				stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		iface_out = p.stdout.read()
		iface_part = iface_out.split(" ")[1]
		return iface_part.split(":")[0]
	except Exception:
		return None
		
def append_host(name, fqdn, iface, hosts):
	ip = iface.attrib["ip"]
	if iface.tag == 'private':
		hosts += '%s\t%s.local %s\n' % (ip, name, name)
	elif iface.tag == 'public':
		hosts += '%s\t%s\n' % (ip, fqdn)
	else:
		hosts += '%s\t%s.%s\n' % (ip, name, iface.tag)
	return hosts

def write_ifcfg(ifname, ip, netmask, mac, mtu, gw = None):
	""" write a ifcfg file with given arguments """
	if not os.path.exists("/etc/sysconfig/network-scripts"):
		print "Wrong OS"
		return
	ifup_str = 'DEVICE=%s\nIPADDR=%s\nNETMASK=%s\n' % (ifname, ip, netmask)
	ifup_str += 'BOOTPROTO=none\nONBOOT=yes\nMTU=%s\n' % mtu
	if mac:
		ifup_str += 'HWADDR=%s\n' % mac
	if gw != None:
		ifup_str += 'GATEWAY=%s\n' % gw
	else:
		ifup_str += 'DEFROUTE=no\n'
	write_file('/etc/sysconfig/network-scripts/ifcfg-%s' % ifname, ifup_str)
 
def write_interfaces(network_info):
	""" write /etc/network/interfaces with given arguments """
	
	if not os.path.exists("/etc/network/interfaces"):
		print "Unable to find existing /etc/network/interfaces file"
		return
	print "Writing /etc/network/interfaces"
	os.rename("/etc/network/interfaces", "/etc/network/interfaces.vc-out-parser.bak")
        interfaces = "auto lo\niface lo inet loopback\n"
	for iface, device in network_info.items():
		interfaces += "auto %s\niface %s inet static\n\taddress %s\n\tnetmask %s\n\tmtu %s\n" % (
			iface, iface, device['ip'], device['netmask'], device['mtu'])
		if "gw" in device:
			interfaces += "\tgateway %s\n" % device['gw']
	write_file('/etc/network/interfaces', interfaces)

def write_file(file_name, content):
	"""write the content in the file_name"""
	f = open(file_name, 'w')
	f.write(content)
	f.close()


if __name__ == "__main__":
    parse()

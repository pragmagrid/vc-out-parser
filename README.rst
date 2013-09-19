Parser for vc-out
-----------------
This script parses the vc-out.xml file and then it create the 
network configuration file used by RHEL based system.

In particular it creates the following files:
/etc/resolv.conf
/etc/sysconfig/network
/etc/hosts
/etc/sysconfig/network-scripts/ifcfg-eth0
/etc/sysconfig/network-scripts/ifcfg-eth1

On the frontend it will also deploy a 
/tmp/machinefile 
which can be used with mpirun to run jobs

For more information on the format of the vc-out.xml
please visit `pragma_boot README file
<https://github.com/pragmagrid/pragma_boot/blob/master/README.rst>`_.


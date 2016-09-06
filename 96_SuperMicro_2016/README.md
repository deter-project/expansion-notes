## August/September 2016

These are some scripts that were written to help with the addition of 96 new
SuperMicro nodes to the DETER testbed in September 2016.


### identify.py

This script contains the bits that were used to map IPMI MAC addresses
to hostnames and collect eth0 mac addresses.  There are really three
'main' functions in it.

 * main()
   * Search a range of IP addresses
	 * If the IP is alive, turn on the chassis UID light using IPMI
     * Prompt the user for the cabinet and rack u of the blinking machine
	 * Map the cabinet and rack u to an ipmi host
	 * Grab the BMC MAC address using RedFish
	 * Write the SQL to update the emulab database with the correct MAC address
	   for the given host a file SQL_OUTPUT

 * check_address() is to verify that mappings are correct
   * Iterate through "sm%d-ipmi" one at a time and blink the chassis LED

 * get_eth0_macs() is to collect, using IPMI, the mac address of the
   control network interface for each node.
    * Go through a range of IPMI BMC hostnames
	* Get the MAC via IPMI
	* Create a dictionary that maps host to mac and mac to host
	* Write dictionary out as a JSON file

### fix_new_nodes.py

This script contains routines for handling switch port discovery and
out of order node discovery:

 * Discovery of the switch and port a host is on using LLDP.  This is
   accomplished by using paramiko and SSHing into the newnode MFS.
 * Proper mapping of hostnames.  Because we know via IPMI what the ctrl/eth0 MAC
   address is of every host, we can easily handle out of order node additions.
 * Make sure the IP address assigned matches the hostname assigned
   (fall out of out of order node discovery)

### bios_key.py

Since we didn't have the proper supermicro tools for automating BIOS
setup, we had to improvise.  All this script does is generate the
right key presses for navigatings and setting the SuperMicro BIOS.  By
logging into the HTML5 KVM and running this script (making sure the
focus is correct) BIOS setup was made much less painful.

### launch_kvm.py

Logging into the SuperMicro KVMs is tedious.  This script uses
selenium to automate the login.  It generally works pretty well, but
once in a while it tickles a race condition of some sort.  You get a
KVM screen, but are actually logged out.  The time.sleeps were an
attempt to work around this.  But overall the script made getting the
job done easier.

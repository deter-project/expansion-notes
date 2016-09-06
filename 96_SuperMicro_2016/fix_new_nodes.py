#!/usr/bin/env python

import logging
import sys
import re
import json

import paramiko
import mysql.connector

MACS="macs.json"

LOGGER = logging.getLogger(__name__)

def load_mac_dict():
    """ Load our dictionary of MAC addresses from JSON """

    with open(MACS) as macs:
        mac_dict = json.load(macs)

    return mac_dict

#
# Hostname Grooming
#
def validate_ip_addresses(cnx):
    """ Ugh """

    nodes_and_ips = """
    SELECT new_node_id, node_id, IP
    FROM new_nodes;
    """

    actions = []

    cursor = cnx.cursor()

    cursor.execute(nodes_and_ips)

    results = cursor.fetchall()
    cursor.close()

    for new_node_id, node_id, ip in results:

        match = re.search("\d+", node_id)

        if not match:
            LOGGER.error("No numbers in %s?!", node_id)
            raise Exception()

        index = match.group(0)

        ip_should_be = "192.168.0.{}".format(index)

        if ip != ip_should_be:
            actions.append("UPDATE new_nodes SET IP='{}' "
                           "WHERE new_node_id={}".format(ip_should_be, new_node_id))
    return actions

def validate_hostnames(cnx):
    """ Idea here is to validate that the hostnames map to mac addresses """

    mac_dict = load_mac_dict()
    actions = []
    cursor = cnx.cursor()

    # Check name mappings

    new_node_macs = """
    SELECT new_nodes.new_node_id, node_id, mac
    FROM new_nodes
    JOIN new_interfaces
    ON new_nodes.new_node_id = new_interfaces.new_node_id
    WHERE card=0;
    """

    cursor.execute(new_node_macs)

    results = cursor.fetchall()

    for new_node_id, node_id, mac in results:

        try:
            # mac_dict is our truth source
            hostname_should_be = mac_dict['mac_to_host'][mac]
        except KeyError:
            LOGGER.exception("Unknown MAC address '%s' from database for id %s",
                             mac,
                             new_node_id)

        # Now compare

        if hostname_should_be != node_id:
            query= "UPDATE new_nodes SET node_id='{}' WHERE new_node_id={};".format(hostname_should_be,
                                                                                    new_node_id)
            actions.append(query)

    return actions

#
# Switch Port Functionality
#

def get_ssh_client(host, username="root", password="muffins"):
    """ Return a Paramiko Client """

    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.client.WarningPolicy())
    client.connect(host, username=username, password=password)

    return client

def get_lldp(client, host):
    """ SSH into a host and use TCP dump to get Switch/Port via LLDP """

    command = "tcpdump -c1 -A -s0 ether proto 0x88cc"

    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read()

    print output

    switch_match = re.search(r"stem\d", output, re.MULTILINE)


    if not switch_match:
        LOGGER.error("Could not find switch in: %s", output)
        raise Exception()

    switch = switch_match.group(0)

    port_match = re.search(r"swp(\d+)", output, re.MULTILINE)

    if not port_match:
        LOGGER.error("Could not find port in: %s", output)
        raise Exception()

    port = port_match.group(1)

    return switch, port

def get_mac_from_host(client, host, interface='igb0'):
    """ SSH into a host and get the MAC address """

    command = "ifconfig {}".format(interface)

    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read()

    match = re.search(r"ether (([0-9a-f]{2}:){5}[0-9a-f]{2})", output, re.MULTILINE)

    if not match:
        LOGGER.error("Could not find mac in: %s", output)
        raise Exception()

    mac = "".join(match.group(1).split(':'))

    return mac.lower()

def get_unset_hosts(cnx):
    """ Grab temp IPs from database for hosts with null macs """

    QUERY = """
    SELECT new_nodes.temporary_IP
    FROM new_nodes
    WHERE new_node_id IN
    (SELECT new_node_id FROM new_interfaces
    WHERE card=0 AND (role != 'ctrl' OR role IS NULL));
    """

    cursor = cnx.cursor()

    cursor.execute(QUERY)

    results = cursor.fetchall()

    cursor.close()

    # get rid of the tuples
    return [x[0] for x in results]

def do_switch_ports(host):
    """ Print out the SQL for a single host """

    client = get_ssh_client(host)

    (switch, port) = get_lldp(client, host)
    mac = get_mac_from_host(client, host)

    unused_mac = get_mac_from_host(client, host, interface='igb1')

    ctrl_sql = ("update new_interfaces set cable=0, len=0, role='ctrl', switch_card=1, "
                "switch_id='{}', switch_port={} where mac='{}';").format(switch, port, mac)

    unused_sql = ("update new_interfaces set cable=0, len=0, role='other', switch_card=0, "
                  "switch_id='NotConnected', switch_port=0 where mac='{}';").format(unused_mac)

    return [ctrl_sql, unused_sql]

def apply_sql(cnx, commands):
    """ Do the SQL """

    cursor = cnx.cursor()

    for command in commands:
        cursor.execute(command)

    cnx.commit()
    cursor.close()

def commit_actions(cnx, actions):
    """ Prompt and act on a list of sql commands """

    if not actions:
        print "No actions required"
        return

    for action in actions:
        print action

    res = raw_input("Shall I commit to the database (y/n)? ")
    if 'y' in res:
        apply_sql(cnx, actions)
    else:
        return
        print "Quitting..."
        sys.exit(1)


def main():
    logging.basicConfig(level=logging.WARN)

    cnx = mysql.connector.connect(host="localhost", db="tbdb")
    actions = []

    LOGGER.info("Mapping switch ports")

    for host in get_unset_hosts(cnx):
        actions.extend(do_switch_ports(host))

    commit_actions(cnx, actions)

    LOGGER.info("Grooming hostnames")

    actions = ["update new_nodes set type='sm';"]
    actions.extend(validate_hostnames(cnx))

    commit_actions(cnx, actions)

    LOGGER.info("Grooming IP addresses")

    actions = validate_ip_addresses(cnx)
    commit_actions(cnx, actions)


if __name__ == "__main__":
    main()

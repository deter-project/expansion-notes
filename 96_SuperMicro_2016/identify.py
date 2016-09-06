#!/usr/bin/env python

import subprocess
import requests
import logging
import json

LOGGER = logging.getLogger(__name__)

SQL_OUTPUT = "/users/jjh/ipmi.sql"

USER="ADMIN"
PASS="ADMIN"

def blink_light(hostname, on=True):
    """ Use IPMITOOL to blink a chassis LED """

    if on:
        opt = "force"
    else:
        opt = "0"

    LOGGER.info("Blinking chassis LED for %s", hostname)

    command = "ipmitool -U {} -P {} -H {} chassis identify {}".format(
        USER, PASS, hostname, opt)

    subprocess.check_call(command, shell=True)

def get_eth0_mac_address(hostname):
    """ Get the MAC for eth0 using IPMI """

    command = "ipmitool -H {} -U ADMIN -P ADMIN raw 0x30 0x21".format(hostname)

    try:
        result = subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as exc:
        LOGGER.exception("Failed to get eth0 mac for %s", hostname)

    # Remove space and newline
    result = result.strip()
    mac = ":".join(result.split()[4:]) # No verification :-(

    return mac

def get_mac_address(hostname):
    """ Get the BMC Mac from RedFish """

    url = "https://{}/redfish/v1/Managers/1/EthernetInterfaces/1/".format(hostname)
    eth_dict = requests.get(url, auth=(USER,PASS),verify=False).json()
    mac_address = eth_dict['MACAddress']

    LOGGER.info("IPMI BMC %s reports MAC address as %s", hostnameh, mac_address)

    return mac_address

def location_to_index():
    """ Prompt and convert cab and ru to a hostname """

    while True:
        cabinet = int(raw_input("Cabinet: "))
        ru = int(raw_input("Rack U: "))

        index = ((cabinet - 1) * 32) + ru

        correct = raw_input("Does index {} sound right (y/n)? ".format(index))

        if 'y' in correct:
            break


    LOGGER.info("Mapping Cabinet: %s, Rack U: %s to %s", cabinet, ru, index)

    return index

def index_to_hostname(index):
    """ Return a hostname """

    hostname = "sm{}-ipmi".format(index)
    LOGGER.info("Index %s -> hostname %s", index, hostname)

    return hostname

def index_to_ip(index):
    """ Return BMC IP """

    last = 100 + index
    ip = "192.168.226.{}".format(last)
    LOGGER.info("BMC IP is %s", ip)
    return ip

def generate_sql(index, mac):
    """ Output our SQL """

    ip = index_to_ip(index)
    hostname = index_to_hostname(index)

    mac = emulab_mac(mac)
    # We use the IP as a safety check
    sql = ("UPDATE interfaces SET mac='{}' WHERE node_id='{}' AND IP='{}';"
    ).format(mac, hostname, ip)

    LOGGER.info("SQL Output: %s", sql)

    with open(SQL_OUTPUT, "a") as sql_out:
        sql_out.write(sql)
        sql_out.write("\n")

def emulab_mac(mac):
    """ Convert to an emulab style mac """

    return "".join(mac.lower().split(':'))

def provision_bmc(hostname):
    """ Stitch together the steps """

    LOGGER.info("Provisioning %s", hostname)

    mac = get_mac_address(hostname)

    blink_light(hostname)

    index = location_to_index()

    generate_sql(index, mac)

    blink_light(hostname, on=False)

def check_alive(hostname):
    """ See if an IP is up """

    LOGGER.info("Seeing if %s is alive", hostname)

    try:
        subprocess.check_call("ping -o -c1 -W1 {}".format(hostname), shell=True)
    except subprocess.CalledProcessError as exc:
        LOGGER.info("Host %s appears down", hostname)
        return False
    else:
        return True

def main():

    logging.basicConfig(level=logging.DEBUG)

    for i in range(100, 231):
        ip = "192.168.224.{}".format(i)
        if check_alive(ip):

            try:
                provision_bmc(ip)
            except: # Requests failed on a non-bmc host
                LOGGER.exception("Failed to provision %s", ip)



def check_address():
    """ Verify that the right node blinks """

    for i in range(1, 97):
        hostname = "sm{}-ipmi".format(i)

        if not check_alive(hostname):
            LOGGER.error("%s is dead", hostname)
        else:
            blink_light(hostname)
            raw_input("Is host {} on? ".format(hostname))
            blink_light(hostname, on=False)

def get_eth0_macs():
    """
    Gather the MAC addresses of eth0 from all SM hosts

    """


    mac_dict = {
        'mac_to_host': {},
        'host_to_mac': {}
    }

    # Host Range
    for i in range(1, 95):

        if i == 47:             # 47 is broken
            continue

        hostname = "sm{}-ipmi".format(i)
        realname = "sm{}".format(i)
        mac = get_eth0_mac_address(hostname).lower()
        mac = emulab_mac(mac)

        mac_dict['host_to_mac'][realname] = mac
        mac_dict['mac_to_host'][mac] = realname

    with open("macs.json", "w") as mac_json:

        json.dump(mac_dict, mac_json, indent=4)


if __name__ == "__main__":
    get_eth0_macs()

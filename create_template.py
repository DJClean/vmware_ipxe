#!/usr/bin/env python3

import argparse
import os
import sys
import sqlite3
import re
from string import Template
import ipaddress

inputfile = None
templatefolder = None
outputfolder = None

def main(arguments):
    global inputfile
    global templatefolder
    global outputfolder

    inputfile = arguments.inputfile
    templatefolder = arguments.templatefolder
    outputfolder = arguments.outputfolder

    if inputfile is None or not os.path.exists(inputfile):
        print("Databasefile (%s) does not exist" % (inputfile))
        sys.exit(1)

    if not os.path.isdir(templatefolder):
        print("Templatefolder (%s) does not exist" % (templatefolder))
        sys.exit(1)

    if not os.path.isdir(outputfolder):
        print("Outputfolder (%s) does not exist, creating!" % (outputfolder))
        os.mkdir(outputfolder)

    #inputfile = '/home/dennis/git/vmware_pxe_tools/db/test.db'
    conn, c = connect(inputfile)

    filepath = '%s/boot' % outputfolder

    if not os.path.isdir(filepath):
        print("Boot folder (%s) does not exist, creating!" % (filepath))
        os.mkdir(filepath)

    menu_file = open('%s/menu.ipxe' % (filepath), 'w')

    for items in build_menu(c):
        menu_file.write(items)

    menu_file.close()

    close(conn)

def build_menu(cursor):

    query = cursor.execute("SELECT DISTINCT(vcenter) FROM hosts")
    template_menu_start = Template(open("%s/ipxe/00-main-start.menu"
                                           % templatefolder).read())
    template_menu_end = Template(open("%s/ipxe/01-main-end.menu"
                                           % templatefolder).read())

    d = {
        'VCENTER': 'unused'
    }

    items = []
    items.append(template_menu_start.template)

    result = query.fetchall()
    menu_items = []
    for row in result:
        vcentername =  row[0]
        for menuitem in build_menu_vcenter(cursor, vcentername):
            menu_items.append(menuitem)
        items.append('item menu-%s %s\n' % (parse_name(vcentername), vcentername))

    items.append(template_menu_end.template)

    for item in menu_items:
        items.append(item)

    return items

def build_menu_vcenter(cursor, vcenter):
    #print("vCenter Menu: %s" % (vcenter))
    query = cursor.execute("SELECT DISTINCT(cluster) FROM hosts \
                           WHERE vcenter = ? \
                           ORDER BY cluster ASC",
                           (vcenter, ))

    template_vcenter_start = Template(open("%s/ipxe/02-menu-vcenter-start.menu"
                                           % templatefolder).read())

    template_vcenter_end = Template(open("%s/ipxe/03-menu-vcenter-end.menu"
                                           % templatefolder).read())

    d = {
        'VCENTER': parse_name(vcenter),
        'VCENTERNAME': vcenter
    }

    items = []

    items.append(template_vcenter_start.substitute(d))

    result = query.fetchall()
    cluster_items = []

    for row in result:
        clustername = row[0]

        for cluster in build_menu_cluster(cursor, clustername):
            cluster_items.append(cluster)
        items.append('item menu-%s %s\n' % (parse_name(clustername), clustername))

    items.append(template_vcenter_end.substitute(d))

    for item in cluster_items:
        items.append(item)

    return items

def build_menu_cluster(cursor, cluster):
    #print("Cluster Menu: %s" % (cluster))

    query = cursor.execute("SELECT DISTINCT(vcenter) FROM hosts \
                           WHERE cluster = ? \
                           ORDER BY host ASC",
                           (cluster, ))

    result = query.fetchone()

    vcenter = result[0]

    template_cluster_start = Template(open("%s/ipxe/04-menu-cluster-start.menu"
                                           % templatefolder).read())

    template_cluster_end = Template(open("%s/ipxe/05-menu-cluster-end.menu"
                                         % templatefolder).read())

    d = {
        'CLUSTER': cluster,
        'PARSEABLE': parse_name(cluster),
        'VCENTER': parse_name(vcenter),
        'VCENTERNAME': vcenter
    }

    items = []

    items.append(template_cluster_start.substitute(d))

    query = cursor.execute("SELECT host FROM hosts \
                           WHERE cluster = ? \
                           ORDER BY host ASC",
                           (cluster, ))

    result = query.fetchall()
    host_items = []

    for row in result:
        host = row[0]
        items.append('item esx-%s  Install %s\n' % (parse_name(strip_name(host)), host))
        host_items.append(build_menu_host(cursor, host))

    items.append(template_cluster_end.substitute(d))

    for item in host_items:
        items.append(item)

    return items

def build_menu_host(cursor, host):
    #print("Processing: %s" % (host))
    template_host = Template(open("%s/ipxe/06-menu-host.menu" % templatefolder).read())

    query = cursor.execute("SELECT version, vlan, cluster, vcenter FROM hosts WHERE host = ?", (host, ))

    result = query.fetchone()

    version = result[0]
    vlan = result[1]
    cluster = result[2]
    vcenter = result[3]

    query = cursor.execute("SELECT bootnetwork FROM vcenters WHERE vcenter = ?", (vcenter, ))

    result = query.fetchone()

    bootnetwork = result[0]

    d = {
        'HOST': host,
        'VERSION': version,
        'VLAN': vlan,
        'CLUSTER': parse_name(cluster),
        'PARSEABLE': parse_name(strip_name(host)),
        'BOOTNETWORK': bootnetwork
    }

    s = template_host.substitute(d)

    query = cursor.execute("SELECT host, ip, gateway, dns, vlan, vmnic FROM hosts \
                           WHERE host = ?", (host, ))

    result = query.fetchone()

    host = result[0]
    ip = ipaddress.ip_interface(result[1])
    ipaddr = ip.ip
    netmask = ip.netmask
    gateway = result[2]
    dns = result[3]
    vlan = result[4]
    vmnic1 = result[5].split(',')[0]
    vmnic2 = result[5].split(',')[1]

    template_kickstart = Template(open("%s/kickstart/default.ks" % templatefolder).read())

    d = {
        'VMHOST': host,
        'IPADDRESS': ipaddr,
        'NETMASK': netmask,
        'GATEWAY': gateway,
        'VLAN': vlan,
        'DNS': dns,
        'UPLINK0': vmnic1,
        'UPLINK1': vmnic2
    }

    ks = template_kickstart.substitute(d)

    filepath = '%s/kickstart' % outputfolder

    if not os.path.isdir(filepath):
        print("Kickstart folder (%s) does not exist, creating!" % (filepath))
        os.mkdir(filepath)

    kickstart_file = open('%s/%s.ks' % (filepath , parse_name(strip_name(host))), 'w')

    kickstart_file.write(ks)
    kickstart_file.close()

    return s

def parse_name(name):
    parsed = re.sub('[^a-zA-Z0-9 \n]', '', name)
    return parsed

def strip_name(name):
    stripped = name.split('.', 1)[0]
    return stripped

def connect(sqlite_file):
    """ Make connection to an SQLite database file """
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    return conn, c

def close(conn):
    """ Commit changes and close connection to the database """
    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file",
                        action="store",
                        dest="inputfile",
                        metavar="DATABASEFILE",
                        default='db/ipxe.db',
                        required=True,
                        help="Database file")

    parser.add_argument("-t", "--templates",
                        action="store",
                        dest="templatefolder",
                        default="templates/",
                        required=True,
                        help="Folder containing all template files")
    parser.add_argument("-o", "--output",
                        action="store",
                        dest="outputfolder",
                        default="output/",
                        help="Folder where output files will be written")

    args = parser.parse_args()
    main(args)

# ipaddress.ip_interface('ip/mask')

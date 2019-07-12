#!/usr/bin/env python3

import argparse
import sqlite3
import os
import sys
import csv

inputfile = None
csvfile = None

def main(arguments):
    global inputfile
    global csvfile

    inputfile = arguments.inputfile
    csvfile = arguments.csvfile
    update = arguments.update

    if inputfile is None or not os.path.exists(inputfile) \
    or not os.path.exists(csvfile) or csvfile is None:
        print("Databasefile (%s) or CSV file (%s) does not exist" %
              (inputfile, csvfile))
        sys.exit(1)

    conn, c = connect(inputfile)

    parse_csv(conn, c, csvfile, update)

    close(conn)

def parse_csv(conn, cursor, filecsv, update):
    with open(filecsv) as file:
        reader = csv.DictReader(file)
        for row in reader:
            hostinfo = {
                'vcenter': row['VCENTER'],
                'cluster': row['CLUSTER'],
                'host': row['HOST'],
                'ip': row['IP'],
                'gateway': row['GATEWAY'],
                'dns': row['DNS'],
                'vlan': row['VLAN'],
                'vmnic': row['VMNIC'],
                'version': row['VERSION'],
                'template': row['TEMPLATE']
            }
            if not check_host(cursor, hostinfo['vcenter'], hostinfo['cluster'],
                              hostinfo['host']):
                print("Should create entry for %s" % (hostinfo['host']))
                create_entry(conn, cursor, hostinfo)

            elif update:
                print("Updating entry %s" % (hostinfo['host']))
                update_entry(conn, cursor, hostinfo)

            else:
                print("Skipping entry as it already exists: %s" %
                      (hostinfo['host']))

def check_host(cursor, vcenter, cluster, host):
    duplicate = False
    query = cursor.execute("SELECT * FROM hosts \
                           WHERE vcenter = ? \
                           AND cluster = ? \
                           AND host = ?",
                           (vcenter, cluster, host))
    result = query.fetchall()

    size = len(result)

    if size > 0:
        duplicate = True

    return duplicate

def create_entry(conn, cursor, hostinfo):
    columns = ', '.join(hostinfo.keys())
    placeholders = ':'+', :'.join(hostinfo.keys())
    #print("INSERT INTO hosts (%s) VALUES (%s)" % (columns, placeholders))
    query = cursor.execute("INSERT INTO hosts (%s) VALUES (%s)" %
                           (columns, placeholders), hostinfo )
    conn.commit()

def update_entry(conn, cursor, hostinfo):
    query = cursor.execute("UPDATE hosts SET cluster=:cluster, ip=:ip, \
                           gateway=:gateway, dns=:dns, vlan=:vlan, \
                           vmnic=:vmnic, version=:version, template=:template \
                           WHERE vcenter = :vcenter AND host = :host", hostinfo)
    conn.commit()

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
                        default="db/ipxe.db",
                        required=True,
                        help="Database file")
    parser.add_argument("-c", "--csv",
                        action="store",
                        dest="csvfile",
                        required=True,
                        help="Input CSV File")
    parser.add_argument("-u", "--update",
                        action="store_true",
                        dest="update"
                        )
    args = parser.parse_args()
    main(args)

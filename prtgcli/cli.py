# -*- coding: utf-8 -*-
"""
CLI Tool for Paessler's PRTG (http://www.paessler.com/)
"""

import argparse
import os
import logging
from prtg.client import Client


def load_config():

    endpoint = None
    username = None
    password = None

    try:
        endpoint = os.environ['PRTGENDPOINT']
        username = os.environ['PRTGUSERNAME']
        password = os.environ['PRTGPASSWORD']
    except KeyError as e:
        print('Unable to load environment variable: {}'.format(e))
        exit(1)

    return endpoint, username, password


def get_response(response):

    from prettytable import PrettyTable

    attribs = list(response[0].__dict__.keys())
    attribs.sort()

    p = PrettyTable(attribs)

    for resp in response:
        p.add_row([resp.__getattribute__(x) for x in attribs])

    return p


def get_parents(response):
    parent_ids = [str(x.parentid) for x in response]
    return '&filter_objid='.join(parent_ids)


def main(args):
    """
    Parse commandline arguments for PRTG-CLI.
    :param args: dict
    :return: None
    """

    logging.basicConfig(level=args.level)

    endpoint, username, password = load_config()

    c = Client(endpoint=endpoint, username=username, password=password)

    if args.command == 'ls':

        q = c.get_table_output(filter_string=args.filterstring, content=args.content)

        if args.parents:  # Lookup the parents of a sensor or device.
            children = c.query(q)
            print(children.response)
        else:
            c.query(q)
            print(get_response(q.response))

    if args.command == 'status':

        q = c.get_status()
        c.query(q)
        print(get_response(q.response))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='PRTG Command Line Interface')
    parser.add_argument('command', type=str, help='command name', choices=['ls', 'status'])
    parser.add_argument('-c', '--content', type=str, help='object type', default='devices',
                        choices=['devices', 'sensors'])
    parser.add_argument('-f', '--filter-string', type=str, dest='filterstring', help='object filter string', default='')
    parser.add_argument('-p', '--parents', action='store_true', help='Lookup parent objects of the sensor or device',
                        default=False)
    parser.add_argument('-s', '--sort-by', type=str, help='Sort by a particular value', default='objid')
    parser.add_argument('-n', '--new-tags', help='Add new tags', dest='newtags')
    parser.add_argument('-l', '--level', help='Logging level', default='INFO')
    main(parser.parse_args())

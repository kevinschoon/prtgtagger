import argparse
import os
from prtg.client import Client

try:
    endpoint = os.environ['PRTGENDPOINT']
    username = os.environ['PRTGUSERNAME']
    password = os.environ['PRTGPASSWORD']
except KeyError as e:
    print('Unable to load environment variable: {}'.format(e))
    exit(1)


def render_table(query):

    def print_row(object_type, name, status, tags):
        _t = [x for x in filter(lambda t: t != '', tags.split(' '))]  # Filter bad tags
        print(" %11s %+25s %+10s %s" % (object_type, name, status, _t))

    query.response.sort(key=lambda x: x.name)
    query.response.sort(key=lambda s: s.status)

    print('total ', len(query.response))
    print(" %11s %+25s %+10s %s" % ('object_type', 'object_name', 'status', 'tags'))
    for index, item in enumerate(query.response):
        print_row(object_type=item.type, name=item.name, status=item.status, tags=item.tags)


def render_object(query):
    print(query.response)


def main(args):

    c = Client(endpoint=endpoint, username=username, password=password)

    if args.command == 'table':
        q = c.get_table_output(filter_string=args.filterstring, content=args.content)
        render_table(c.query(q))

    if args.command == 'status':
        q = c.get_status()
        render_object(c.query(q))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PRTG Command Line Interface')
    parser.add_argument('command', type=str, help='command name', choices=['table', 'status'])
    parser.add_argument('-c', '--content', type=str, help='object type', default='devices',
                        choices=['devices', 'sensors'])
    parser.add_argument('-f', '--filter-string', type=str, dest='filterstring', help='object filter string', default='')
    main(parser.parse_args())

# -*- coding: utf-8 -*-

"""
Bulk tag updater tool for the PRTG (http://www.paessler.com/) API.
"""

import requests
import argparse


class BadRequest(Exception):
    pass


class Sensor(object):
    def __init__(self, **kwargs):
        self.name = None
        for key in SearcherTool.queries['sensors']['columns']:
            self.__setattr__(key, kwargs[key])


class Device(object):
    def __init__(self, **kwargs):
        self.name = None
        for key in SearcherTool.queries['devices']['columns']:
            self.__setattr__(key, kwargs[key])


class SearcherTool(object):

    queries = {
        'sensors': {
            'args': ['content=sensors', 'output=json'],
            'columns': ['objid', 'parentid', 'name', 'type', 'sensor', 'tags'],
            'target': 'api/table.json?'
        },
        'devices': {
            'args': ['content=devices', 'output=json'],
            'columns': ['objid', 'name', 'type', 'host', 'device', 'tags'],
            'target': 'api/table.json?'
        },
        'setobjectproperty': {
            'args': [],
            'columns': [],
            'target': 'api/setobjectproperty.htm?'
        }
    }

    def __init__(self, endpoint, username, password, limit=500):
        self.endpoint = endpoint
        self.username = username
        self.password = password
        self.limit = limit
        self._counter = 0
        self.finished = False

    def auth_string(self):
        return 'username={}&password={}&'.format(self.username, self.password)

    def count(self, count, total):
        print('Processed {}/{} objects'.format(self._counter, total))
        if self._counter + count >= total:
            self.finished = True
            self._counter = 0
            return
        self._counter += count

    def _get_result_set(self, url, counter_item):
        response = self.get(url)
        self.count(len(response[counter_item]), response['treesize'])
        return response

    def _url(self, query, **kwargs):

        print('kwargs:', kwargs)

        url = '{}/{}{}&count={}&start={}'.format(
            self.endpoint,
            query['target'],
            self.auth_string(),
            self.limit,
            str(self._counter)
        )

        if query['args']:
            url += '&' + '&'.join(query['args'])

        if query['columns']:
            url += '&columns=' + ','.join(query['columns'])

        if kwargs:
            url += '&' + '&'.join(map(lambda x: '{}={}'.format(x[0], x[1]), filter(lambda z: z[1], kwargs.items())))

        return url

    def get(self, url):
        req = requests.get(url)
        if req.status_code != 200:
            raise BadRequest(req)
        print(req)
        return req.json()

    def post(self, url):
        req = requests.post(url)
        if req.status_code != 200:
            raise BadRequest(req)
        return True

    def query(self, query_type, **kwargs):

        while not self.finished:
            resp = self._get_result_set(self._url(self.queries[query_type], **kwargs), counter_item=query_type)
            yield resp

    def lookup_device(self, objid):
        args = {'filter_objid': objid}
        result = self.get(self._url(self.queries['devices'], **args))
        if result['devices']:
            return result['devices'].pop()
        else:
            raise BadRequest('No device with objid: {} was found'.format(objid))

    def set_object_property(self, device_id, name, value):
        print('Updating device properties: ')
        _update = {'name': name, 'value': value, 'id': device_id}
        url = self._url(self.queries['setobjectproperty'], **_update)
        return self.post(url)


def lookup_sensor(searcher, tags=None, objid=None):

    sensors = list()

    print(searcher, type(searcher))

    for sensor in searcher.query(query_type='sensors', filter_tags=tags, filter_objid=objid):
        sensors.extend([Sensor(**x) for x in sensor['sensors']])

    return sensors


def lookup_device(searcher, tags=None, objid=None):

    devices = list()

    for device in searcher.query(query_type='devices', filter_tags=tags, filter_objid=objid):
        devices.extend([Device(**x) for x in device['devices']])

    return devices


def tag_sensor_parents(searcher, sensors, new_tags):

    job_map = dict()

    for sensor in sensors:

        if sensor.parentid in job_map:
            continue

        job_map[sensor.parentid] = {'sensor': sensor, 'device': None, 'updated': False}

    for parent in job_map.keys():
        device = Device(**searcher.lookup_device(parent))
        results([device])
        job_map[parent]['device'] = device

    print('PLEASE REVIEW YOUR CHANGES BEFORE CONTINUING:')
    for _id, value, in job_map.items():
        print('{}: DEVICE: {} Will update tags: {}'.format(_id, value['device'].name, new_tags.split(' ')))
        ui = raw_input('Continue? (Y/N) ')
        if ui != 'Y':
            raise BaseException("User Canceled")
        print(searcher.set_object_property(_id, name='tags', value=new_tags))


def results(out, job_map=None):

    for index, result in enumerate(out):
        print('{}({}): '.format(result.type, str(index)) + ', '.join([result.name, result.tags]))


def main(args):
    searcher = SearcherTool(endpoint=args.endpoint, username=args.username, password=args.password, limit=500)

    if args.tag_sensor_parents:
        sensors = lookup_sensor(searcher, tags=args.tags, objid=args.objid)
        tag_sensor_parents(searcher=searcher, sensors=sensors, new_tags=args.new_tags)
        return

    if args.device:
        out = lookup_device(searcher, args.tags, args.objid)
        results(out)
        return

    if args.sensor:
        out = lookup_sensor(searcher, args.tags, args.objid)
        results(out)
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PRTG CLI')
    parser.add_argument('--endpoint', help='PRTG API endpoint', required=True)
    parser.add_argument('--username', help='PRTG username', required=True)
    parser.add_argument('--password', help='PRTG password', required=True)
    parser.add_argument('--sensor', action='store_true', help='Search for a sensor object')
    parser.add_argument('--device', action='store_true', help='Search for a device object')
    parser.add_argument('--tags', help='Search by a tag string')
    parser.add_argument('--objid', help='Search by an objid')
    parser.add_argument('--new_tags', help='New tags separated by commas')
    parser.add_argument('--tag-sensor-parents', action='store_true',
                        help='Lookup a sensors by tag and then tag all its parents with new tags')

    main(parser.parse_args())

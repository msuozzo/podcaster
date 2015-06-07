"""Tests for the Datetime JSON decoder
"""
from podcaster.datetime_json import DatetimeDecoder, DatetimeEncoder

import unittest
import json
from datetime import datetime


class DatetimeDecoderTests(unittest.TestCase):
    def test_without_date(self):
        d = json.loads('{"Foo": {"Bar": "Baz"}}', cls=DatetimeDecoder)
        self.assertEquals({'Foo': {'Bar': 'Baz'}}, d)

    def test_with_date(self):
        time_dict = {'Time': datetime.now()}
        json_str = json.dumps(time_dict, cls=DatetimeEncoder)
        decoded_dict = json.loads(json_str, cls=DatetimeDecoder)
        self.assertIsInstance(decoded_dict['Time'], datetime)

    def test_with_other_hook(self):
        def hook(obj):
            if isinstance(obj, dict) and u'__Foo__' in obj:
                return ' '.join((obj['Bar'], obj['Baz']))
            return obj
        dict_ = {'Time': datetime.now()}
        dict_['Foo'] = {'__Foo__': True, 'Bar': 'Hello', 'Baz': 'World!'}
        json_str = json.dumps(dict_, cls=DatetimeEncoder)
        decoded_dict = json.loads(json_str, cls=DatetimeDecoder, object_hook=hook)
        self.assertEquals(decoded_dict['Foo'], 'Hello World!')
        self.assertIsInstance(decoded_dict['Time'], datetime)


class DatetimeEncoderTests(unittest.TestCase):
    def test_without_date(self):
        encoded = json.dumps({'Foo': {'Bar': 'Baz'}}, cls=DatetimeEncoder)
        self.assertEquals(encoded, '{"Foo": {"Bar": "Baz"}}')

    def test_with_date(self):
        date = datetime.now()
        time_dict = {'Time': date}
        json_str = json.dumps(time_dict, cls=DatetimeEncoder)
        parsed_dict = json.loads(json_str)
        self.assertSetEqual(set(parsed_dict['Time'].keys()), set(['ISO-8601', '__datetime__']))
        self.assertEqual(parsed_dict['Time']['ISO-8601'], date.isoformat())

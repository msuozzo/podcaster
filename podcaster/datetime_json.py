"""Support for JSON encoding and decoding of python datetime objects
"""
import json
from datetime import datetime

from dateutil import parser


class DatetimeDecoder(json.JSONDecoder):
    """JSON decoder with support for encoded datetime objects.
    """
    def __init__(self, *args, **kwargs):
        super(DatetimeDecoder, self).__init__(*args, **kwargs)
        self._old_hook = self.object_hook
        self.object_hook = self._as_datetime

    def _as_datetime(self, dict_):
        """If `dict_` is a JSON-encoded datetime object, decode it.
        Else, pass `dict_` to the object_hook.
        """
        if '__datetime__' in dict_:
            return parser.parse(dict_['ISO-8601'])
        return self._old_hook(dict_)


class DatetimeEncoder(json.JSONEncoder):
    """JSON encoder that supports datetime objects
    """
    def default(self, obj): #pylint: disable=method-hidden
        if isinstance(obj, datetime):
            return {'__datetime__': True, 'ISO-8601': obj.isoformat()}
        return super(DatetimeEncoder, self).default(obj)

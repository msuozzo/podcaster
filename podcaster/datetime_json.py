"""Support for JSON encoding and decoding of python datetime objects
"""
import json
from datetime import datetime

from dateutil import parser


class DatetimeDecoder(json.JSONDecoder):
    """JSON decoder with support for encoded datetime objects.

    WARNING: All object hooks used in addition to this Decoder _MUST_ check
            that the hook parameter is a dict before attempting to decode it.

            An additional check of `isinstance(param, dict)` will suffice to
            avoid decode conflicts.
    """
    def __init__(self, *args, **kwargs):
        if len(args) >= 2:
            hook = args[1]
            args[1] = lambda dict_: hook(DatetimeDecoder.as_datetime(dict_))
        elif 'object_hook' in kwargs:
            hook = kwargs['object_hook']
            kwargs['object_hook'] = lambda dict_: hook(DatetimeDecoder.as_datetime(dict_))
        else:
            kwargs['object_hook'] = DatetimeDecoder.as_datetime
        super(DatetimeDecoder, self).__init__(*args, **kwargs)

    @staticmethod
    def as_datetime(obj):
        """If `dict_` is a JSON-encoded datetime object, decode it.
        Else, pass `dict_` to the object_hook.
        """
        if isinstance(obj, dict) and u'__datetime__' in obj:
            return parser.parse(obj[u'ISO-8601'])
        return obj


class DatetimeEncoder(json.JSONEncoder):
    """JSON encoder that supports datetime objects
    """
    def default(self, obj): #pylint: disable=method-hidden
        if isinstance(obj, datetime):
            return {'__datetime__': True, 'ISO-8601': obj.isoformat()}
        return super(DatetimeEncoder, self).default(obj)

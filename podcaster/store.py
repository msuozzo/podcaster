"""Object/File stores
"""
from datetime_json import DatetimeEncoder, DatetimeDecoder

import os
import json
from datetime import datetime

from dateutil.tz import tzutc


class InitializationError(BaseException):
    """Indicates initialization of the store failed
    """
    pass


class SimpleFileStore(object):
    """A basic file store with metadata stored in an on-disk JSON manifest
    """
    _MANIFEST_FNAME = '.manifest.json'

    def __init__(self, store_dir):
        self._manifest_fname = SimpleFileStore._MANIFEST_FNAME
        self._store_dir = os.path.abspath(store_dir)
        self._manifest_path = os.path.join(self._store_dir, self._manifest_fname)
        self._manifest = {}

        self._load_dir()
        self._load_manifest()
        self._validate()

    def _load_manifest(self):
        """Load (and, if necessary, initialize) the store's manifest
        """
        if os.path.exists(self._manifest_path):
            if not os.path.isfile(self._manifest_path):
                raise InitializationError('Unable to load store manifest "%s": Path exists '
                        'and is not a file' % self._manifest_path)
            elif not os.access(self._manifest_path, os.R_OK | os.W_OK):
                raise InitializationError('Unable to load store manifest "%s": Insufficient '
                        'access permissions' % self._manifest_path)
        else:
            # If the manifest does not exist, write it out to file before loading it
            self.save()
        with open(self._manifest_path, 'r') as manifest_file:
            try:
                self._manifest = json.load(manifest_file, cls=DatetimeDecoder)
            except ValueError:
                raise InitializationError('Corrupted manifest file')

    def _load_dir(self):
        """Load (and, if necessary, initialize) the store directory
        """
        if os.path.exists(self._store_dir):
            if not os.path.isdir(self._store_dir):
                raise InitializationError('Requested store dir "%s" exists '
                        'and is not a dir' % self._store_dir)
            elif not os.access(self._store_dir, os.R_OK | os.W_OK):
                raise InitializationError('Insufficient access permissions to '
                        'requested store dir "%s"' % self._store_dir)
        else:
            try:
                os.makedirs(self._store_dir)
            except OSError:
                raise InitializationError('Failed to create store dir at "%s"' % self._store_dir)

    def _validate(self):
        """Check for consistency between the loaded manifest and the backing store
        """
        # Remove any manifest entries whose paths no longer exist
        paths = set()
        for key, entry in self._manifest.items():
            if not os.path.exists(entry['path']):
                del self._manifest[key]
            paths.add(entry['path'])
        # Remove any unlisted files
        for fname in os.listdir(self._store_dir):
            if fname not in paths and fname != self._manifest_fname:
                os.remove(os.path.join(self._store_dir, fname))

    def save(self):
        """Save the file metadata to disk (i.e. recoverable when loaded again)
        """
        with open(self._manifest_path, 'w') as manifest_file:
            json.dump(self._manifest, manifest_file, cls=DatetimeEncoder, sort_keys=True, indent=4)

    @staticmethod
    def _key_to_fname(key):
        """Return a valid file name for `key`
        """
        return str(hash(key))

    def put(self, key, data):
        """Store a key mapped to some data

        key - the string to be mapped to `data`
        data - the data to be associated with `key`
        """
        if self.exists(key):
            self.remove(key)
        fname = self._key_to_fname(key)
        path = os.path.join(self._store_dir, fname)
        while os.path.exists(path):
            fname = self._key_to_fname(fname)
            path = os.path.join(self._store_dir, fname)
        with open(path, 'wb') as data_file:
            data_file.write(data)
        self._manifest[key] = {'added': datetime.now(tzutc()), 'path': path}

    def get_path(self, key):
        """If key is valid, return the file system path to the data file
        """
        return self._manifest[key]['path'] if self.exists(key) else None

    def get_date_added(self, key):
        """Return a datetime object representing the moment at which the key
        was added to the store.
        """
        return self._manifest[key]['added'] if self.exists(key) else None

    def remove(self, key):
        """If the key exists in the store, remove the key and data.
        Else, do nothing.

        key - the key to be removed from the store
        """
        if self.exists(key):
            os.remove(self.get_path(key))
            del self._manifest[key]

    def exists(self, key):
        """Return whether the key `key` exists in the store
        """
        return key in self._manifest

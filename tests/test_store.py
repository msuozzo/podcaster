"""Tests for the Datetime JSON decoder
"""
from podcaster import store
from podcaster.store import SimpleFileStore, InitializationError
from tests.utils import TempDir

import unittest
import os
import datetime
from datetime import datetime, timedelta
from dateutil.tz import tzutc


class InitStoreTests(unittest.TestCase):
    def setUp(self):
        self._store_dir = 'dir'
        self._manifest_path = os.path.join(self._store_dir, SimpleFileStore._MANIFEST_FNAME)
        self._temp_dir = TempDir()
        self._temp_dir.enter()

    def tearDown(self):
        self._temp_dir.exit()

    def _in_good_state(self):
        self.assertTrue(os.path.exists(self._store_dir))
        self.assertTrue(os.path.exists(self._manifest_path))

    def test_bare(self):
        dummy_fs = SimpleFileStore(self._store_dir)
        self._in_good_state()

    def test_existing_dir(self):
        os.mkdir(self._store_dir)
        dummy_fs = SimpleFileStore(self._store_dir)
        self._in_good_state()

    def test_existing_dir_unreachable(self):
        self._store_dir = 'dir'
        os.mkdir(self._store_dir, 0000)
        self.assertRaises(InitializationError, SimpleFileStore, self._store_dir)

    def test_dir_exists_as_file(self):
        open(self._store_dir, 'w').close()
        self.assertRaises(InitializationError, SimpleFileStore, self._store_dir)

    def test_dir_unreadable(self):
        prefix = 's'
        os.mkdir(prefix)
        os.chdir(prefix)
        os.chmod('.', 0000)
        self.assertRaises(InitializationError, SimpleFileStore, self._store_dir)

    def test_dir_uncreatable(self):
        prefix = 's'
        os.mkdir(prefix)
        os.chmod(prefix, 0000)
        self._store_dir = os.path.join(prefix, self._store_dir)
        self.assertRaises(InitializationError, SimpleFileStore, self._store_dir)

    def test_existing_manifest(self):
        os.mkdir(self._store_dir)
        SimpleFileStore(self._store_dir)
        self._in_good_state()

    def test_existing_manifest_unreachable(self):
        os.mkdir(self._store_dir)
        open(self._manifest_path, 'w').close()
        os.chmod(self._manifest_path, 0000)
        self.assertRaises(InitializationError, SimpleFileStore, self._store_dir)

    def test_existing_manifest_corrupted(self):
        os.mkdir(self._store_dir)
        with open(self._manifest_path, 'w') as manifest:
            manifest.write('{')
        self.assertRaises(InitializationError, SimpleFileStore, self._store_dir)

    def test_manifest_exists_as_dir(self):
        os.mkdir(self._store_dir)
        os.mkdir(self._manifest_path)
        self.assertRaises(InitializationError, SimpleFileStore, self._store_dir)


class SimpleFileStoreTests(unittest.TestCase):

    def setUp(self):
        self._temp_dir = TempDir()
        self._temp_dir.enter()

        self._store_dir = 'dir'
        self.store = SimpleFileStore(self._store_dir)

    def tearDown(self):
        self._temp_dir.exit()

    def test_keys(self):
        self.store.put('k1', 'v')
        self.assertSetEqual(set(self.store.keys()), set(['k1']))
        self.assertTrue(all(self.store.exists(key) for key in self.store.keys()))
        self.store.put('k2', 'v')
        self.assertSetEqual(set(self.store.keys()), set(['k1', 'k2']))
        self.assertTrue(all(self.store.exists(key) for key in self.store.keys()))

    def test_reload(self):
        self.store.put('k', 'v')
        self.store.save()
        other_fs = SimpleFileStore(self._store_dir)
        self.assertSetEqual(set(other_fs.keys()), set(['k']))

    def test_validate(self):
        self.store.put('k', 'v')
        self.store.save()
        garbage_fname = os.path.join(self._store_dir, 'foo')
        open(garbage_fname, 'w').close()
        dummy = SimpleFileStore(self._store_dir)
        self.assertTrue(not os.path.exists(garbage_fname))

        os.remove(self.store.get_path('k'))
        dummy = SimpleFileStore(self._store_dir)
        self.assertTrue(not dummy.exists('k'))

    def test_date_added(self):
        expected = datetime.now(tzutc())
        self.store.put('k', 'v')
        date = self.store.get_date_added('k')
        self.assertAlmostEqual(date, expected, delta=timedelta(seconds=1))

    def test_remove(self):
        self.store.put('k', 'v')
        path = self.store.get_path('k')
        self.store.remove('k')
        self.assertTrue(not self.store.exists('k'))
        self.assertTrue(not os.path.exists(path))

    def test_put_twice(self):
        self.store.put('k', 'v1')
        self.store.put('k', 'v2')
        self.assertEqual(len(self.store.keys()), 1)
        self.assertEqual(open(self.store.get_path('k')).read(), 'v2')

    def test_no_save_put(self):
        self.store.put('k', 'v')
        path = self.store.get_path('k')

        # Changes not saved
        dummy = SimpleFileStore(self._store_dir)
        self.assertTrue(not dummy.exists('k'))
        self.assertTrue(not os.path.exists(path))

    def test_put(self):
        self.store.put('k', 'v')
        self.assertEqual(open(self.store.get_path('k')).read(), 'v')
        self.store.save()

        dummy = SimpleFileStore(self._store_dir)
        self.assertEqual(open(dummy.get_path('k')).read(), 'v')

    def test_put_file(self):
        with open('foo', 'w') as file_:
            file_.write('v')
        with open('foo', 'rb') as file_:
            self.store.put('k', file_)
        self.assertEqual(open(self.store.get_path('k')).read(), 'v')
        self.store.save()

        dummy = SimpleFileStore(self._store_dir)
        self.assertEqual(open(dummy.get_path('k')).read(), 'v')

    def test_put_bad_file(self):
        with self.assertRaises(IOError):
            with open('foo', 'w') as file_:
                file_.write('v')
                self.store.put('k', file_)

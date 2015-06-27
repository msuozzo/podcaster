"""Tests for the Datetime JSON decoder
"""
from podcaster import player
from tests.utils import TempDir

import unittest
from time import sleep
from contextlib import contextmanager
import os


class PlayerTest(unittest.TestCase):
    def setUp(self):
        reload(player)
        self._default_media_path = 'file://%s/tests/files/point1sec.mp3' %\
                                            os.path.abspath(os.curdir)
        self._default_media_length = .1
        self._temp_dir = TempDir()
        self._temp_dir.enter()

    def _load_media(self, a_player, media=None):
        media_path = self._default_media_path if media is None else media
        a_player.change_media('foo', media_path)

    @contextmanager
    def _get_player(self, quiet=True):
        if quiet:
            with player.VLCPlayer.init_no_log() as a_player:
                yield a_player
        else:
            yield player.VLCPlayer()

    def tearDown(self):
        self._temp_dir.exit()

    def test_finished(self):
        with self._get_player() as a_player:
            self._load_media(a_player)
            a_player.play()
            sleep(self._default_media_length + .3)
            self.assertTrue(a_player.is_finished())
            a_player.stop()

    def test_stop(self):
        with self._get_player() as a_player:
            self._load_media(a_player)
            a_player.play()
            a_player.stop()
            self.assertFalse(a_player.is_playing())

    def test_playback_rate(self):
        with self._get_player() as a_player:
            self._load_media(a_player)
            a_player.play()
            a_player.set_playback_rate(.1)
            self.assertEqual(a_player.get_playback_rate(), .1)
            a_player.set_playback_rate(0)
            self.assertEqual(a_player.get_playback_rate(), .1)
            a_player.set_playback_rate(20)
            self.assertEqual(a_player.get_playback_rate(), .1)
            a_player.stop()

    def test_position(self):
        with self._get_player() as a_player:
            self._load_media(a_player)
            a_player.play()
            a_player.set_position(-1)
            self.assertEqual(a_player.get_position(), 0)
            a_player.set_position(.01)
            self.assertEqual(a_player.get_position(), .01)
            a_player.stop()

    def test_play_async(self):
        with self._get_player() as a_player:
            self._load_media(a_player)
            a_player.play_async()
            self.assertFalse(a_player.is_playing())
            sleep(.05)
            self.assertTrue(a_player.is_playing())
            a_player.stop()

    def test_play(self):
        with self._get_player() as a_player:
            self._load_media(a_player)
            a_player.play()
            self.assertTrue(a_player.is_playing())
            a_player.stop()

    def test_no_log(self):
        player.devnull = 'foo'
        with self._get_player() as a_player:
            try:
                self._load_media(a_player, 'file:///this/is/a/fake/path')
            except player.MediaError:
                pass
        with open('foo') as sink:
            self.assertNotEqual(sink.read(), '')

    def test_bad_uri(self):
        with self._get_player() as a_player:
            with self.assertRaises(player.MediaError):
                self._load_media(a_player, 'file:///this/is/a/fake/path')

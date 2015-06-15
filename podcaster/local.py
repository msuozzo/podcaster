"""Metadata manager for the podcasts and episodes
"""
from podcaster.http import download_to_file, ConnectionError
from podcaster.datetime_json import DatetimeEncoder, DatetimeDecoder
from podcaster.store import SimpleFileStore

import os
import json
from datetime import datetime

from dateutil import parser
from dateutil.tz import tzutc


class PodcastManager(object):
    """Manages the local files and metadata for the podcasts
    """
    _MANIFEST_FNAME = '.podcaster.json'

    def __init__(self, storage_dir='.podcasts'):
        self._store = SimpleFileStore(storage_dir)
        self._manifest_fname = PodcastManager._MANIFEST_FNAME
        self._manifest = {}
        self._init_manifest()

    def _init_manifest(self):
        """Initialize the manifest by reading the manifest file or creating one if none is found
        """
        if not os.path.exists(self._manifest_fname):
            self._manifest = {}
            self.save()
        with open(self._manifest_fname) as manifest_file:
            self._manifest = json.load(manifest_file, cls=DatetimeDecoder)

    def save(self):
        """Ensure all state is written to disk (i.e. recoverable when loaded again)
        """
        self._store.save()
        with open(self._manifest_fname, 'w') as manifest_file:
            json.dump(self._manifest, manifest_file, cls=DatetimeEncoder, sort_keys=True, indent=4)

    def links(self):
        """Return each podcasts' rss link
        """
        return {name: data['rss_url'] for name, data in self._manifest.iteritems()}

    def add_podcast(self, podcast):
        """Add a podcast to the local state
        """
        self._manifest[podcast.name] = {
                'last_checked': parser.parse('1/1/1970 00:01:00+0000'),
                'episode_data': {},
                'rss_url': podcast.rss_url,
                'preferred_playback_rate': 1.0
            }

    def has_update(self, podcast):
        """Return whether the Podcast object has been updated since it was last checked
        """
        return self._manifest[podcast.name]['last_checked'] < podcast.last_updated

    def register_checked(self, podcast):
        """Register the Podcast object as having been checked.
        """
        self._manifest[podcast.name]['last_checked'] = datetime.now(tzutc())

    def get_preferred_playback_rate(self, podcast):
        """If a local copy of `episode` exists, return the date added.
        Else, return None.
        """
        return self._manifest[podcast.name]['preferred_playback_rate']

    def set_preferred_playback_rate(self, podcast, rate):
        """If a local copy of `episode` exists, return the date added.
        Else, return None.
        """
        self._manifest[podcast.name]['preferred_playback_rate'] = rate

    @staticmethod
    def _to_store_key(episode):
        """Derives a storage key from an Episode instance
        """
        return ' - '.join((episode.podcast_name, episode.title))

    def is_downloaded(self, episode):
        """Return whether a local copy of the Episode `episode` exists.
        """
        key = PodcastManager._to_store_key(episode)
        return self._store.exists(key)

    def get_local_uri(self, episode):
        """If a local copy of `episode` exists, return the URI.
        Else, return None.
        """
        key = PodcastManager._to_store_key(episode)
        if self._store.exists(key):
            return 'file://' + self._store.get_path(key)
        return None

    def get_date_added(self, episode):
        """If a local copy of `episode` exists, return the date added.
        Else, return None.
        """
        key = PodcastManager._to_store_key(episode)
        if self._store.exists(key):
            return self._store.get_date_added(key)
        return None

    def download_episode(self, episode, cb_progress=None):
        """Download an episode to the local machine

        On success: the local path to the episode
        On failure: None

        Args:
            episode: the `Episode` instance to download
            cb_progress: a callback function accepting a single parameter.
                If the download progress is available, this parameter will be
                the current download progress expressed as a number between 0.0
                and 1.0 (1.0 being complete).
                If the progress is not available, this parameter will be None.
        """
        local_episodes = self._manifest[episode.podcast_name]['episode_data']
        episode_dict = {'last_position': None}
        local_episodes[episode.title] = episode_dict

        # Define callback closure to convert download callback format to progress format
        if cb_progress is not None:
            def cb_report(chunk_num, chunk_size, total_size):
                """Return the completion ratio of the download if available.
                Else, return None
                """
                if total_size != -1:
                    cb_progress((1. * chunk_size * chunk_num) / total_size)
                else:
                    cb_progress(None)
        else:
            cb_report = None

        # Attempt download
        try:
            local_fname, _ = download_to_file(episode.url, reporthook=cb_report)
        except ConnectionError:
            return None
        else:
            key = PodcastManager._to_store_key(episode)
            with open(local_fname, 'rb') as file_:
                self._store.put(key, file_)
            return self.get_local_uri(episode)

    def _get_episode_dict(self, episode):
        """Return the dict containging data about `episode`

        KeyError if episode dict not found
        """
        return self._manifest[episode.podcast_name]['episode_data'][episode.title]

    def set_episode_position(self, episode, curr_seconds):
        """Record the position (in seconds) of an episode being played
        """
        self._get_episode_dict(episode)['last_position'] = curr_seconds

    def get_last_position(self, episode):
        """If the podcast was stopped during playback, return the second offset
            at which it was stopped.
        Else, return None.
        """
        return self._get_episode_dict(episode)['last_position']

    def finish_episode(self, episode):
        """Record that an episode is complete by resetting the `last_position` data
        """
        self.set_episode_position(episode, None)

    def delete_episode(self, episode):
        """Delete local file and references to an episode
        """
        key = PodcastManager._to_store_key(episode)
        self._store.remove(key)
        del self._manifest[episode.podcast_name]['episode_data'][episode.title]

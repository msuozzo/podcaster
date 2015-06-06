from http import download_to_file
from datetime_json import DatetimeEncoder, DatetimeDecoder

import os
import json
from datetime import datetime

from dateutil import parser
from dateutil.tz import tzutc


#TODO: Refactor the os operations to another class
#TODO: Refactor everything. This is a monstrosity.
class PodcastFileManager(object):
    """Manages the local files and metadata for the podcasts
    """
    def __init__(self, storage_dir='.podcasts', manifest_fname='.manifest.json'):
        self.storage_dir = os.path.abspath(storage_dir)
        self.manifest_fname = manifest_fname
        self._manifest_path = os.path.join(self.storage_dir, self.manifest_fname)
        self._manifest = {}
        self._init_storage()
        self._init_manifest()
        #TODO: Verify episode paths

    def _init_storage(self):
        """Initialize the storage directory
        """
        #TODO: Handle invalid path (i.e. a file)
        if not os.path.isdir(self.storage_dir):
            os.makedirs(self.storage_dir)

    def _dump_manifest(self):
        """Dump the current contents of the manifest dictionary to disk
        """
        with open(self._manifest_path, 'w') as manifest_file:
            json.dump(self._manifest, manifest_file, cls=DatetimeEncoder, sort_keys=True, indent=4)

    def _init_manifest(self):
        """Initialize the manifest by reading the manifest file or creating one if none is found
        """
        if not os.path.exists(self._manifest_path):
            self._manifest = {}
            self._dump_manifest()
        with open(self._manifest_path) as manifest_file:
            self._manifest = json.load(manifest_file, cls=DatetimeDecoder)

    def close(self):
        """Ensure all state is written to disk (i.e. recoverable when loaded again)
        """
        self._dump_manifest()

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
                'rss_url': podcast.rss_url
            }

    def is_updated(self, podcast):
        """Return whether the Podcast object has been updated since it was last checked
        """
        return self._manifest[podcast.name]['last_checked'] < podcast.last_updated

    def check(self, podcast):
        """Register the Podcast object as having been checked.
        """
        self._manifest[podcast.name]['last_checked'] = datetime.now(tzutc())

    def is_downloaded(self, episode):
        """Return whether a local copy of the Episode `episode` exists.
        """
        return episode.title in self._manifest[episode.podcast_name]['episode_data']

    def get_local_uri(self, episode):
        if self.is_downloaded(episode):
            return self._get_episode_dict(episode)['uri']
        else:
            return None

    def download_episode(self, episode):
        """Download an episode to the local machine

        On success: the local path to the episode
        On failure: None
        """
        local_episodes = self._manifest[episode.podcast_name]['episode_data']
        episode_dict = {'last_position': None}
        remote_fname = episode.url.rsplit('/', 1)[-1]
        local_path = os.path.join(self.storage_dir, remote_fname)
        episode_dict['uri'] = 'file://' + local_path
        local_episodes[episode.title] = episode_dict
        return download_to_file(episode.url, local_path)

    def _get_episode_dict(self, episode):
        return self._manifest[episode.podcast_name]['episode_data'][episode.title]

    def play_episode(self, episode, curr_seconds):
        """Record the position (in seconds) of an episode being played
        """
        self._get_episode_dict(episode)['last_position'] = curr_seconds

    def get_last_position(self, episode):
        return self._get_episode_dict(episode)['last_position']

    def finish_episode(self, episode):
        """Record that an episode is complete by resetting the `last_position` data
        """
        self.play_episode(episode, None)

    def delete_episode(self, episode):
        """Delete local file and references to an episode
        """
        local_episodes = self._manifest[episode.podcast_name]['episode_data']
        os.remove(local_episodes[episode.title]['uri'])
        del local_episodes[episode.title]

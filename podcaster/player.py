"""Media players
"""
from podcaster.vlc import MediaPlayer, get_default_instance, PyFile_AsFile

from contextlib import contextmanager


class Player(object):
    """An abstract class providing a media player interface.
    """
    def change_media(self, name, uri):
        """Change the media being played

        Args:
            name: Name of the media being loaded
            uri: URI of the media being loaded
        """
        raise NotImplementedError

    def get_media_name(self):
        """Return the name of the currently loaded media
        """
        raise NotImplementedError

    def get_media_length(self):
        """Return the length of the media in seconds
        """
        raise NotImplementedError

    def play(self):
        """Play the media
        """
        raise NotImplementedError

    def pause(self):
        """Pause the media
        """
        raise NotImplementedError

    def stop(self):
        """Stop media playback
        """
        raise NotImplementedError

    def is_playing(self):
        """Return whether the media is playing
        """
        raise NotImplementedError

    def is_finished(self):
        """Return whether the media has concluded
        """
        raise NotImplementedError

    def set_playback_rate(self, new_rate):
        """Set the playback rate of the media

        new_rate - the new playback rate (1.0 is normal speed)
        """
        raise NotImplementedError

    def get_playback_rate(self):
        """Get the current playback rate
        """
        raise NotImplementedError

    def move_playback_rate(self, rate_offset):
        """Move the playback position of the media

        rate_offset - a +/- number by which to adjust the rate (1.0 is normal speed)
            NOTE: This number is relative to the normal rate, not the current rate.
                i.e. rate=1.5; move_playback_rate(.1) --> 1.6
        """
        self.set_playback_rate(self.get_playback_rate() + rate_offset)

    def set_position(self, seconds):
        """Set the playback position of the media
        NOTE: This function should be bounds checked. `move_position` uses it blindly

        seconds - the second offset from the start of the media from which to
                    play
        """
        raise NotImplementedError

    def get_position(self):
        """Get the current playback position as a second offset from the start
        of the media
        """
        raise NotImplementedError

    def move_position(self, position_offset):
        """Move the playback position of the media

        position_offset - a +/- number of seconds to adjust the playback position
        """
        self.set_position(self.get_position() + position_offset)


class VLCPlayer(Player):
    """A Player backed by libvlc's MediaPlayer
    """
    def __init__(self):
        super(VLCPlayer, self).__init__()
        self._player = MediaPlayer()
        self._media_name = ''

    @staticmethod
    @contextmanager
    def init_no_log(*args, **kwargs):
        """Context for an instance of VLCPlayer which emits no log messages.

        Args: VLCPlayer constructor arguments
        """
        with open('/dev/null', 'w') as sink:
            get_default_instance().log_set_file(PyFile_AsFile(sink))
            yield VLCPlayer(*args, **kwargs)

    def change_media(self, name, uri):
        media = get_default_instance().media_new(uri)
        self._player.set_media(media)
        self._media_name = name

    def get_media_name(self):
        return self._media_name

    def get_media_length(self):
        return self._player.get_length() / 1000

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()

    def is_playing(self):
        return self._player.is_playing()

    def is_finished(self):
        return self.get_position() == self.get_media_length()

    def set_playback_rate(self, new_rate):
        if new_rate > 0. and new_rate <= 10.:
            self._player.set_rate(new_rate)

    def get_playback_rate(self):
        return self._player.get_rate()

    def set_position(self, seconds):
        seconds = max(seconds, 0)
        self._player.set_time(1000 * seconds)

    def get_position(self):
        return self._player.get_time() / 1000

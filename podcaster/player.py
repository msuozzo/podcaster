"""Media players
"""
from podcaster.vlc import MediaPlayer, get_default_instance, PyFile_AsFile, EventType, State

from contextlib import contextmanager
from os import devnull
from copy import copy


class MediaError(Exception):
    """Indicates an error with the media loaded into the player.
    """
    pass


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

    Because of the imprecision of the C-to-Python floating-point
    value conversions, this class limits the precision of the
    playback rate and position (seconds elapsed) to 4 decimal places.
    """
    def __init__(self):
        super(VLCPlayer, self).__init__()
        self._player = MediaPlayer()
        self._media_name = ''
        self._vlc_event = self._player.event_manager()
        self._last_event = None

    @staticmethod
    @contextmanager
    def init_no_log(*args, **kwargs):
        """Context for an instance of VLCPlayer which emits no log messages.

        Args: VLCPlayer constructor arguments
        """
        with open(devnull, 'w') as sink:
            get_default_instance().log_set_file(PyFile_AsFile(sink))
            yield VLCPlayer(*args, **kwargs)

    @contextmanager
    def _set_event_handler(self, event_type):
        """Sets an event handler for a vlc.EventType value

        `self._last_event` will be set with any matching events that occur in
        the scope of the context.

        event_type: a vlc.EventType value
        """
        def cb_event_handler(event):
            """Set the object's last event to the type of `event`
            """
            # Memory becomes invalid without a copy here (causes segfault)
            self._last_event = copy(event.type)

        self._vlc_event.event_attach(event_type, cb_event_handler)
        yield
        self._vlc_event.event_detach(event_type)
        self._last_event = None

    def change_media(self, name, uri):
        media = get_default_instance().media_new(uri)
        self._player.set_media(media)
        self._media_name = name
        with self._set_event_handler(EventType.MediaPlayerEncounteredError):
            with self._set_event_handler(EventType.MediaPlayerPausableChanged):
                self.play_async()
                while self._last_event is None:
                    pass
                if self._last_event == EventType.MediaPlayerEncounteredError:
                    raise MediaError('Failed to load media "%s" from "%s"' % (name, uri))
                self.stop()

    def get_media_name(self):
        return self._media_name

    @staticmethod
    def _round(val):
        """Round floating point values to 4 decimal places
        """
        return round(val, 4)

    def get_media_length(self):
        return VLCPlayer._round(self._player.get_length() / 1000.)

    def play(self):
        with self._set_event_handler(EventType.MediaPlayerPlaying):
            self.play_async()
            while self._last_event is None:
                pass

    def play_async(self):
        """Return immediately after issuing the play command.
        NOTE: media may not be playing upon return
        """
        self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()

    def is_playing(self):
        return self._player.is_playing()

    def is_finished(self):
        return self._player.get_state() == State.Ended

    def set_playback_rate(self, new_rate):
        if new_rate > 0. and new_rate <= 10.:
            self._player.set_rate(new_rate)

    def get_playback_rate(self):
        return VLCPlayer._round(self._player.get_rate())

    def set_position(self, seconds):
        millis = VLCPlayer._round(1000. * max(seconds, 0.))
        self._player.set_time(int(millis))

    def get_position(self):
        return VLCPlayer._round(self._player.get_time() / 1000.)

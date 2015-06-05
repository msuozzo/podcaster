from vlc import MediaPlayer, get_default_instance, PyFile_AsFile

import signal
from itertools import chain


class Player(object):
    """An abstract class providing a media player interface.
    """
    def __init__(self, uri=''):
        pass

    def change_media(self, uri):
        """Change the media being played
        """
        raise NotImplementedError()

    def get_media_length(self):
        """Return the length of the media in seconds
        """
        raise NotImplementedError()

    def play(self):
        """Play the media
        """
        raise NotImplementedError()

    def is_playing(self):
        """Return whether the media is playing
        """
        raise NotImplementedError()

    def pause(self):
        """Pause the media
        """
        raise NotImplementedError()

    def set_playback_rate(self, new_rate):
        """Set the playback rate of the media

        new_rate - the new playback rate (1.0 is normal speed)
        """
        raise NotImplementedError()

    def get_playback_rate(self):
        """Get the current playback rate
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def get_position(self):
        """Get the current playback position as a second offset from the start
        of the media
        """
        raise NotImplementedError()

    def move_position(self, position_offset):
        """Move the playback position of the media

        position_offset - a +/- number of seconds to adjust the playback position
        """
        self.set_position(self.get_position() + position_offset)


class VLCPlayer(Player):
    """A Player backed by libvlc's MediaPlayer
    """
    def __init__(self, uri=''):
        super(VLCPlayer, self).__init__(uri)
        self._player = MediaPlayer()
        if uri:
            self.change_media(uri)

    def change_media(self, uri):
        media = get_default_instance().media_new(uri)
        self._player.set_media(media)

    def get_media_length(self):
        return self._player.get_length() / 1000

    def play(self):
        self._player.play()

    def is_playing(self):
        return self._player.is_playing()

    def pause(self):
        self._player.pause()

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


class CmdLineController(object):
    """A Player controller using an interactive terminal to retrieve input.
    """
    TIMEOUT = 1
    PROMPT = '> '

    def __init__(self, player, update_callback=lambda player: 1):
        self._player = player
        self._update_callback = update_callback
        self.commands = {
                "ff": ("advance 30 seconds", lambda: self._player.move_position(30)),
                "f": ("advance 10 seconds", lambda: self._player.move_position(10)),
                "p": ("pause", self._player.pause),
                "l": ("play", self._player.play),
                "gp": ("print current position", self._print_position),
                "gr": ("print current playback rate", self._print_playback_rate),
                "h": ("print help", self._print_help),
                "b": ("rewind 10 seconds", lambda: self._player.move_position(-10)),
                "bb": ("rewind 30 seconds", lambda: self._player.move_position(-30)),
                "ir": ("increase the rate of playback by 10%", lambda: self._player.move_playback_rate(.1)),
                "dr": ("decrease the rate of playback by 10%", lambda: self._player.move_playback_rate(-.1)),
                "q": ("exit playback", self.quit)
            }
        self._interrupted = False
        self._finished = False

    def run(self):
        """Run the command loop
        """
        with open('/dev/null', 'w') as sink:
            get_default_instance().log_set_file(PyFile_AsFile(sink))

            # register interrupt handler
            interrupt = lambda signum, frame: 1
            signal.signal(signal.SIGALRM, interrupt)
            self._player.play()
            self._finished = False
            while not self._finished:
                self._interrupted = False
                while not self._attempt_command():
                    self._interrupted = True

    def _get_command(self):
        cmd = raw_input(CmdLineController.PROMPT if not self._interrupted else '')
        if cmd not in self.commands:
            return None
        else:
            return self.commands[cmd][1]

    def _attempt_command(self):
        signal.alarm(CmdLineController.TIMEOUT)
        try:
            func = self._get_command()
        except OSError:
            return False
        else:
            # disable alarm
            signal.alarm(0)
            if func is not None:
                func()
            else:
                print 'Invalid Command'
                self._print_help()
            return True
        finally:
            # This is tricky:
            # If playback finishes, end the player regardless of the user command
            if self._player.get_position() == self._player.get_media_length():
                self._finished = True
                return True
            self._update_callback(self._player)

    def _print_playback_rate(self):
        print "Playback rate: %1.1f" % self._player.get_playback_rate()

    def _print_position(self):
        print "Position: %d / %d" % (self._player.get_position(), self._player.get_media_length())

    def _print_help(self):
        help_header = ("Commands:",)
        command_help = ("\t{}\t{}".format(cmd, help_)
                            for cmd, (help_, _) in sorted(self.commands.items()))
        print "\n".join(chain(help_header, command_help))

    def quit(self):
        self._finished = True

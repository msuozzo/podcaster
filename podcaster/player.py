import signal

from vlc import MediaPlayer

from itertools import chain


class Player(object):
    TIMEOUT = 1
    PROMPT = '> '
    #TODO: Add update_callback
    def __init__(self, uri, update_callback=None):
        self.media_uri = uri
        self._player = MediaPlayer(uri)
        self._playing = False
        self._interrupted = False
        self._finished = False
        self.update_callback = update_callback
        self.commands = {
                "ff": ("advance 30 seconds", lambda: self.set_position(self.get_position() + 30)),
                "f": ("advance 10 seconds", lambda: self.set_position(self.get_position() + 10)),
                "p": ("pause", self.pause),
                "l": ("play", self.play),
                "gp": ("print current position", self._print_position),
                "gr": ("print current playback rate", self._print_playback_rate),
                "h": ("print help", self._print_help),
                "b": ("rewind 10 seconds", lambda: self.set_position(self.get_position() - 10)),
                "bb": ("rewind 30 seconds", lambda: self.set_position(self.get_position() - 30)),
                "ir": ("increase the rate of playback by 10%", lambda: self.set_playback_rate(self.get_playback_rate() + .1)),
                "dr": ("decrease the rate of playback by 10%", lambda: self.set_playback_rate(self.get_playback_rate() - .1)),
                "q": ("exit playback", self.quit)
            }

    def _get_command(self):
        cmd = raw_input(Player.PROMPT if not self._interrupted else '')
        if cmd not in self.commands:
            return None
        else:
            return self.commands[cmd][1]

    def run(self, start_position=0):
        """Run the command loop
        start_position - the second offset from the start of the file from which to start playback
        """
        # register interrupt handler
        interrupt = lambda signum, frame: 1
        signal.signal(signal.SIGALRM, interrupt)
        self.play()
        if start_position:
            self.set_position(start_position)
        self._finished = False
        while not self._finished:
            self._interrupted = False
            while not self._attempt_command():
                self._interrupted = True

    def _attempt_command(self):
        signal.alarm(Player.TIMEOUT)
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
            # This is tricky: regardless of user command, if playback finishes, end the player
            if self._player.get_position() == 1.:
                self._finished = True
                return True
            self.update_callback()

    def play(self):
        self._player.play()
        self._playing = True
        return True

    def pause(self):
        if self._player.is_playing() and self._playing:
            self._player.pause()
            self._playing = False
            return True
        return False

    def set_playback_rate(self, new_rate):
        if new_rate > 0. and new_rate <= 10.:
            self._player.set_rate(new_rate)

    def get_playback_rate(self):
        return self._player.get_rate()

    def _print_playback_rate(self):
        print "Playback rate: %1.1f" % self.get_playback_rate()

    def set_position(self, seconds):
        seconds = max(seconds, 0)
        self._player.set_time(1000 * seconds)
        self.play()

    def get_position(self):
        return self._player.get_time() / 1000

    def _print_position(self):
        print "Position: %d / %d" % (self.get_position(), self._player.get_length() / 1000)

    def _print_help(self):
        help_header = ("Commands:",)
        command_help = ("\t{}\t{}".format(cmd, help_)
                            for cmd, (help_, _) in sorted(self.commands.items()))
        print "\n".join(chain(help_header, command_help))

    def quit(self):
        self._finished = True

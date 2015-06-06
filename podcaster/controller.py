"""Controllers for `Player` objects
"""
import signal
from itertools import chain


class TimeoutError(BaseException):
    """Indicates a timeout
    """
    pass


class TimeoutInput(object):
    """An terminal input utility that expires after a fixed number of seconds
    """
    def __init__(self, prompt='> ', timeout=1):
        self.timeout = timeout
        self.prompt = prompt
        # register interrupt handler
        def cb_interrupt(signum, frame):
            """Raise a TimeoutError if SIGALRM is encountered
            """
            if signum == signal.SIGALRM:
                raise TimeoutError()
        signal.signal(signal.SIGALRM, cb_interrupt)

    def get_input(self, print_prompt=True):
        """Prompt the user for input.
        If the user responds within `self.timeout` seconds, return the user's input.
        Else, return None.

        print_prompt - print the prompt string (`self.prompt`).
                        If operation timed out previously, prompt should be
                        False so the prompt string will not be printed twice.
        """
        signal.alarm(self.timeout)
        try:
            input_ = raw_input(self.prompt if print_prompt else '')
        except TimeoutError:
            return None
        else:
            # disable alarm
            signal.alarm(0)
            return input_


class CmdLineController(object):
    """A Player controller using an interactive terminal to retrieve input.
    """
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
                "ir": ("increase the rate of playback by 10%",
                        lambda: self._player.move_playback_rate(.1)),
                "dr": ("decrease the rate of playback by 10%",
                        lambda: self._player.move_playback_rate(-.1)),
                "q": ("exit playback", lambda: None)
            }
        self._interrupted = False
        self._finished = False
        self._input_getter = TimeoutInput()

    def run(self, initial_position=None):
        """Run the command loop
        """
        self._player.play()
        if initial_position is not None:
            self._player.set_position(initial_position)
        while True:
            cmd = self._input_getter.get_input(print_prompt=not self._interrupted)
            self._update_callback(self._player)
            # If playback finishes, end the player regardless of the user command
            if self._player.is_finished() or cmd == 'q':
                break
            self._interrupted = cmd is None
            if cmd in self.commands:
                self.commands[cmd][1]()
            elif not self._interrupted:
                print 'Invalid Command'
                self._print_help()

    def _print_playback_rate(self):
        """Print the current playback rate
        """
        print "Playback rate: %1.1f" % self._player.get_playback_rate()

    def _print_position(self):
        """Print the current playback position
        """
        print "Position: %d / %d" % (self._player.get_position(), self._player.get_media_length())

    def _print_help(self):
        """Print all possible commands with their help messages
        """
        help_header = ("Commands:",)
        command_help = ("\t{}\t{}".format(cmd, help_)
                            for cmd, (help_, _) in sorted(self.commands.items()))
        print "\n".join(chain(help_header, command_help))

"""Controllers for `Player` objects
"""
from podcaster.io import AsyncCmdLineIO

from itertools import chain


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
        self._input_getter = AsyncCmdLineIO(timeout=5)

    def run(self, initial_rate=None, initial_position=None):
        """Run the command loop
        """
        initial_rate = 1.0 if initial_rate is None else initial_rate
        if initial_position is not None:
            print 'Skip to %d seconds in (y/N)' % initial_position
            cmd = self._input_getter.input_('? ')
            use_initial_position = cmd == 'y'
        else:
            use_initial_position = False

        self._player.play()
        while not self._player.is_playing():
            pass
        # initialize playback
        if use_initial_position:
            self._player.set_position(initial_position)
        self._player.set_playback_rate(initial_rate)
        # print help
        self._print_position()
        self._print_playback_rate()
        self._print_help()

        while True:
            cmd = self._input_getter.async_input('> ' if not self._interrupted else '')
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
        self._player.stop()

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

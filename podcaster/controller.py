"""Controllers for `Player` objects
"""
from podcaster.io import AsyncCmdLineIO
from podcaster.menu import build_menu


def _format_time(seconds):
    """Return a string representing `seconds` in hours, minutes, and seconds
    """
    hrs = seconds // 3600
    seconds -= 3600 * hrs
    mins = seconds // 60
    seconds -= 60 * mins
    return '%02dh%02dm%02ds' % (hrs, mins, seconds)


class CmdLineController(object):
    """A Player controller using an interactive terminal to retrieve input.
    """
    def __init__(self, player, update_callback=lambda player: None):
        self._player = player
        self._update_callback = update_callback
        self._command_list = (
                ('ff', ('advance 30 seconds', lambda: self._player.move_position(30))),
                ('f', ('advance 10 seconds', lambda: self._player.move_position(10))),
                ('p', ('toggle play/pause', self._player.pause)),
                ('b', ('rewind 10 seconds', lambda: self._player.move_position(-10))),
                ('bb', ('rewind 30 seconds', lambda: self._player.move_position(-30))),
                ('+r', ('increase the rate of playback by 10%',
                        lambda: self._player.move_playback_rate(.1))),
                ('-r', ('decrease the rate of playback by 10%',
                        lambda: self._player.move_playback_rate(-.1))),
                ('q', ('exit playback', lambda: None))
        )
        self._command_help = [(cmd, help_) for cmd, (help_, _) in self._command_list]
        self.commands = dict(self._command_list)
        self._io = AsyncCmdLineIO(timeout=5)

    def run(self, initial_rate=1.0, initial_position=None):
        """Run the command loop
        """
        if initial_position is not None:
            cmd = self._io.input_('Skip to %d seconds in (y/N)? ' % initial_position)
            use_initial_position = cmd == 'y'
        else:
            use_initial_position = False
        # initialize playback
        self._player.play()
        if use_initial_position:
            self._player.set_position(initial_position)
        self._player.set_playback_rate(initial_rate)
        interrupted = False
        while True:
            if not interrupted:
                self._io.print_(self._status_menu())
            cmd = self._io.async_input('> ' if not interrupted else '')
            self._update_callback(self._player)
            # If playback finishes, end the player regardless of the user command
            if self._player.is_finished() or cmd == 'q':
                break
            interrupted = cmd is None
            if cmd in self.commands:
                self.commands[cmd][1]()
            elif not interrupted and cmd:
                self._io.print_('Invalid Command')
        self._player.stop()

    def _status_menu(self):
        """Return a menu displaying the current state of the playback as well
        as the commands available to the user.
        """
        title = 'Now Playing: %s' % self._player.get_media_name()
        stats = (
                ('Playback rate', '%1.1fx' % self._player.get_playback_rate()),
                ('Elapsed', _format_time(self._player.get_position())),
                ('Total Length', _format_time(self._player.get_media_length())),
        )
        return '\n'.join((build_menu(title, action_rows=stats),
                            build_menu('Commands', action_rows=self._command_help)))

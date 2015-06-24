from podcaster.player import VLCPlayer
from podcaster.controller import CmdLineController
from podcaster.menu import build_data_rows, build_menu
from podcaster.io import CmdLineIO

from operator import attrgetter


class ASCIIView(object):
    def __init__(self, controller, io_cls=CmdLineIO):
        self.controller = controller
        self._io = io_cls()

    def _menu_action(self, page_text, actions):
        self._io.print_(page_text)
        choice = self._get_valid_choice(actions.keys())
        return actions[choice]

    def _get_valid_choice(self, valid_choices):
        fail_str = 'Failed. Valid Commands: {%s}' % ', '.join(list(sorted(valid_choices)))
        while True:
            choice = raw_input('> ')
            if choice not in valid_choices:
                self._io.print_(fail_str)
            else:
                return choice

    def update(self):
        self._io.print_('Updating...')

    def add_podcast(self):
        while True:
            url = self._io.input_('Enter Podcast URL (empty to cancel): ')
            if not url:
                break
            self._io.print_('Retrieving feed information')
            new_podcast = self.controller.get_podcast_name(url)
            if new_podcast is None:
                self._io.print_('Failed to extract a Podcast RSS feed from URL')
            elif self._io.input_('Add "%s" (y/N)? ' % new_podcast) == 'y':
                self.controller.new_podcast(url)
                self._io.print_('Successfully added "%s"' % new_podcast)
                break
            else:
                self._io.print_('Not adding "%s"' % new_podcast)
        return self.controller.all_podcasts


    def all_podcasts(self, podcasts):
        # Build menu data
        new_series = ('New?',
                        lambda podcast: '[X]' if podcast.has_update() else "[ ]",
                        lambda f: f)
        name_series = ('Podcast',
                        attrgetter('name'),
                        lambda f: f)

        to_key = lambda i: str(i + 1)
        data_rows = build_data_rows(to_key, podcasts, new_series, name_series)
        # Build menu actions
        cb_return_menu = self.controller.all_podcasts
        other_actions = {
                'a': ('Add a new podcast URL', self.controller.add_podcast),
                'u': ('Update All Podcasts', lambda: self.controller.update_podcasts(cb_return_menu)),
                't': ('View Downloaded Episodes', self.controller.downloaded_episodes),
                'q': ('Quit', None)
            }
        action_rows = [(cmd, desc) for cmd, (desc, _) in other_actions.iteritems()]
        # Build menu page
        page_text = build_menu('All Podcasts', data_rows, action_rows)

        # Build action table
        actions = {}
        for ind, podcast in enumerate(podcasts):
            pid = podcast.id
            actions[to_key(ind)] = lambda p=pid: self.controller.episodes(p)
        for cmd, (_, action) in other_actions.iteritems():
            actions[cmd] = action

        return self._menu_action(page_text, actions)

    def episodes(self, podcast, episodes, episode_range):
        date_series = ("Date",
                        attrgetter('date_published'),
                        lambda field: field.strftime('%m/%d'))
        dld_series = ("DLD?",
                        lambda episode: "[%s]" % ("X" if episode.local_file is not None else " "),
                        lambda f: f)
        title_series = ("Episode",
                        attrgetter('title'),
                        lambda f: f)
        to_key = lambda i: str(i + 1)
        data_rows = build_data_rows(to_key, episodes, date_series, dld_series, title_series)
        # Build menu actions
        cb_return_menu = lambda p=podcast.id: self.controller.episodes(p, episode_range[0])
        other_actions = {
                'b': ('Back to All Podcasts', self.controller.all_podcasts),
                'u': ('Update', lambda: self.controller.update_podcast(podcast.id, cb_return_menu)),
                'd{n}': ('Delete an Episode', lambda: None),
                'q': ('Quit', None)
            }
        if episode_range[1] is not None:
            other_actions['n'] = ('Next Page', lambda: self.controller.episodes(podcast.id, episode_range[1]))
        if episode_range[0] != 0:
            other_actions['p'] = ('Previous Page', lambda: self.controller.episodes(podcast.id, episode_range[0] - 10))
        action_rows = [(cmd, desc) for cmd, (desc, _) in other_actions.iteritems()]
        # Build menu page
        page_text = build_menu(podcast.name + ' Episodes', data_rows, action_rows)

        actions = {}
        for ind, episode in enumerate(episodes):
            eid = episode.id
            actions[to_key(ind)] = lambda e=eid: self.controller.play(e, cb_return_menu)
            actions['d' + to_key(ind)] = lambda e=eid: self.controller.delete_episode(e, cb_return_menu)
        del other_actions['d{n}']
        for cmd, (_, action) in other_actions.iteritems():
            actions[cmd] = action

        return self._menu_action(page_text, actions)

    def downloaded_episodes(self, episodes, episode_range):
        # extract the 10 episodes prior to `base`
        date_series = ("Date",
                        lambda e: e.local_file.date_created,
                        lambda field: field.strftime('%m/%d'))
        title_series = ("Episode",
                        attrgetter('title'),
                        lambda f: f)
        podcast_series = ("Podcast",
                        attrgetter('podcast_name'),
                        lambda f: f)
        to_key = lambda i: str(i + 1)
        data_rows = build_data_rows(to_key, episodes, date_series, title_series, podcast_series)
        # Build menu actions
        other_actions = {
                'b': ('Back to All Podcasts', self.controller.all_podcasts),
                'd{n}': ('Delete an Episode', lambda: None),
                'q': ('Quit', None)
            }

        action_rows = [(cmd, desc) for cmd, (desc, _) in other_actions.iteritems()]
        # Build menu page
        page_text = build_menu('Downloaded Episodes', data_rows, action_rows)

        actions = {}
        cb_return_menu = self.controller.downloaded_episodes
        for ind, episode in enumerate(episodes):
            eid = episode.id
            actions[to_key(ind)] = lambda e=eid: self.controller.play(e, cb_return_menu)
            actions['d' + to_key(ind)] = lambda e=eid: self.controller.delete_episode(e, cb_return_menu)
        del other_actions['d{n}']
        for cmd, (_, action) in other_actions.iteritems():
            actions[cmd] = action

        return self._menu_action(page_text, actions)

    def download(self, episode):
        self._io.print_('Downloading %s....' % episode.title)
        # Create a closure around mutable `current_progress`
        current_progress = [.0]
        progress_step = .1
        def cb_progress(ratio):
            """Output the download progress at intervals of `progress_step`

            Modification of `current_progress` element allows state to
            persist across calls so that progress output can be triggered
            at set increments.
            """
            if ratio is not None and current_progress[0] < ratio:
                self._io.write('%d%% ' % (100 * ratio))
                self._io.flush()
                current_progress[0] += progress_step
        success = self.controller.download_episode(episode.id, cb_progress)
        if not success:
            self._io.print_('\nDownload failed')
        else:
            self._io.print_('\nDownload complete!\n')
        return success

    def play(self, podcast, episode, cb_return_menu):
        """Launch the Player to play `episode`
        """
        player = VLCPlayer(episode.local_file.uri)
        def cb_update_position(player):
            """Update the playback position periodically.
            """
            self.controller.update_episode_state(episode.id,
                    player.get_position(),
                    player.get_playback_rate())
        controller = CmdLineController(player, cb_update_position)
        controller.run(initial_rate=podcast.playback_rate,
                        initial_position=episode.last_position)

        return cb_return_menu

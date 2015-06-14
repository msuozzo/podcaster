from podcaster.local import PodcastManager
from podcaster.rss import get_podcast
from podcaster.player import VLCPlayer
from podcaster.controller import CmdLineController
from podcaster.table import TextTable

from operator import attrgetter
from itertools import ifilter, chain


def build_data_rows(ind_to_key, obj_lst, *series_args):
    """

    *series_args: 3-tuples of (series_name, obj_to_data, data_to_str)
        where the latter two elements are functions converting each object to
        data and the data to a string, respectively.
    """
    rows = [['CMD'] + [name for name, _, _ in series_args]]
    for ind, obj in enumerate(obj_lst):
        row = [ind_to_key(ind)] + [fmt(extract(obj)) for _, extract, fmt in series_args]
        rows.append(row)
    return rows


def build_menu(title, data_rows, action_rows):
    menu = TextTable()

    # Add table title
    menu.add_break_row(seps=('+', '+'))
    menu.add_row((title,), align='c', seps=('|', '|'))
    menu.add_break_row(seps=('+', '+'))

    # Add data section
    num_series = len(data_rows[0]) - 2
    name_seps = ('|', '|') + num_series * ('|',) + ('|',)
    header_seps = ('+', '+') + num_series * ('v',) + ('+',)
    data_seps = ('|', '|') + num_series * (' ',) + ('|',)
    footer_seps = ('+', '+') + num_series * ('^',) + ('+',)
    menu.add_row(data_rows[0], align='c', seps=name_seps)
    menu.add_break_row(seps=header_seps)
    menu.set_seps(*data_seps)
    for data_row in data_rows[1:]:
        menu.add_row(data_row)
    if len(data_rows) == 1:
        menu.add_row(('There\'s nothing here...',), seps=('?', '?'))
    menu.add_break_row(seps=footer_seps)

    # Add action section
    menu.set_seps('|', '|', '|')
    for action_row in action_rows:
        menu.add_row(action_row)
    menu.add_break_row(seps=('+', '+', '+'))

    return str(menu)


class Podcaster(object):
    QUIT = -1
    PROMPT = "> "
    def __init__(self):
        self.manager = PodcastManager()
        self.podcasts = []

    def run(self):
        self.update()
        current_menu = self.all_podcasts
        while current_menu != Podcaster.QUIT:
            print
            current_menu = current_menu()
        self.manager.save()

    def _get_choice(self, valid_choices):
        choice = None
        while True:
            choice = raw_input(Podcaster.PROMPT)
            if choice not in valid_choices:
                print "Failed. Valid Commands: {%s}" % ", ".join(list(sorted(valid_choices)))
            else:
                return choice

    def all_podcasts(self):
        # Build menu data
        new_series = ("New?", lambda f: f,
                        lambda podcast: '[X]' if self.manager.has_update(podcast) else "[ ]")
        name_series = ("Podcast", attrgetter('name'), lambda f: f)
        to_key = lambda i: str(i + 1)
        data_rows = build_data_rows(to_key, self.podcasts, new_series, name_series)
        # Build menu actions
        other_actions = {
                'a': ('Add a new podcast URL', self.add_podcast),
                't': ('View Downloaded Episodes', self.downloaded_podcasts),
                'q': ('Quit', Podcaster.QUIT)
            }
        action_rows = [(cmd, desc) for cmd, (desc, _) in other_actions.iteritems()]
        # Build menu
        menu_text = build_menu('All Podcasts', data_rows, action_rows)

        # Build action table
        actions = {}
        for ind, podcast in enumerate(self.podcasts):
            actions[to_key(ind)] = lambda p=podcast: self.episodes(p)
        for cmd, (_, action) in other_actions.iteritems():
            actions[cmd] = action

        print menu_text

        choice = self._get_choice(actions.keys())
        return actions[choice]

    def add_podcast(self):
        url = raw_input('Enter URL (empty to cancel): ')
        if url:
            print 'Retrieving feed information'
            #TODO: Error Handling
            new_podcast = get_podcast(url)
            add_check = raw_input('Add "%s" (y/N)? ' % new_podcast.name)
            if add_check == 'y':
                self.manager.add_podcast(new_podcast)
                self.podcasts.append(new_podcast)
                print 'Successfully added "%s"' % new_podcast.name
            else:
                print 'Not adding "%s"' % new_podcast.name
        return self.all_podcasts

    def episodes(self, podcast, base=0):
        self.manager.register_checked(podcast)

        # Build menu data
        by_date = sorted(podcast.episodes.values(), key=lambda p: p.date_published)
        # extract the 10 episodes prior to `base`
        episodes = list(reversed(by_date))[base:base + 10]
        date_series = ("Date",
                        attrgetter('date_published'),
                        lambda field: field.strftime('%m/%d'))
        dld_series = ("DLD?",
                        lambda f: f,
                        lambda field: "[%s]" % ("X" if self.manager.is_downloaded(field) else " "))
        title_series = ("Episode",
                        attrgetter('title'),
                        lambda f: f)
        to_key = lambda i: str(i + 1)
        data_rows = build_data_rows(to_key, episodes, date_series, dld_series, title_series)
        # Build menu actions
        other_actions = {
                'b': ('Back to All Podcasts', self.all_podcasts),
                'q': ('Quit', Podcaster.QUIT)
            }
        if base + 10 <= len(podcast.episodes):
            other_actions['n'] = ('Next Page', lambda: self.episodes(podcast, base + 10))
        if base > 0:
            other_actions['p'] = ('Previous Page', lambda: self.episodes(podcast, base - 10))
        action_rows = [(cmd, desc) for cmd, (desc, _) in other_actions.iteritems()]
        # Build menu
        menu_text = build_menu(podcast.name, data_rows, action_rows)

        actions = {}
        cb_return_menu = lambda: self.episodes(podcast, base)
        for ind, episode in enumerate(episodes):
            actions[to_key(ind)] = lambda e=episode: self.play(e, cb_return_menu)
        for cmd, (_, action) in other_actions.iteritems():
            actions[cmd] = action

        print menu_text

        choice = self._get_choice(actions.keys())
        return actions[choice]

    def downloaded_podcasts(self):
        # Build menu data
        all_episodes = chain.from_iterable(podcast.episodes.values() for podcast in self.podcasts)
        downloaded_episodes = ifilter(lambda e: self.manager.is_downloaded(e), all_episodes)
        by_date = list(reversed(sorted(downloaded_episodes,
                                        key=lambda e: self.manager.get_date_added(e))))

        # extract the 10 episodes prior to `base`
        date_series = ("Date",
                        lambda e: self.manager.get_date_added(e),
                        lambda field: field.strftime('%m/%d'))
        title_series = ("Episode",
                        attrgetter('title'),
                        lambda f: f)
        podcast_series = ("Podcast",
                        attrgetter('podcast_name'),
                        lambda f: f)
        to_key = lambda i: str(i + 1)
        data_rows = build_data_rows(to_key, by_date, date_series, title_series, podcast_series)
        # Build menu actions
        other_actions = {
                'b': ('Back to All Podcasts', self.all_podcasts),
                'q': ('Quit', Podcaster.QUIT)
            }

        action_rows = [(cmd, desc) for cmd, (desc, _) in other_actions.iteritems()]
        # Build menu
        menu_text = build_menu('Downloaded Episodes', data_rows, action_rows)

        actions = {}
        cb_return_menu = self.downloaded_podcasts
        for ind, episode in enumerate(by_date):
            actions[to_key(ind)] = lambda e=episode: self.play(e, cb_return_menu)
        for cmd, (_, action) in other_actions.iteritems():
            actions[cmd] = action

        print menu_text

        choice = self._get_choice(actions.keys())
        return actions[choice]

    def play(self, episode, cb_return_menu):
        """Launch the Player to play `episode`
        """
        if not self.manager.is_downloaded(episode):
            print 'Downloading %s....' % episode.title
            #TODO: Error checking
            self.manager.download_episode(episode)
        uri = self.manager.get_local_uri(episode)
        player = VLCPlayer(uri)
        by_name = {podcast.name: podcast for podcast in self.podcasts}
        podcast = by_name[episode.podcast_name]
        def cb_update_position(player):
            """Update the playback position periodically.
            """
            self.manager.set_episode_position(episode, player.get_position())
            self.manager.set_preferred_playback_rate(podcast,
                                                        player.get_playback_rate())
        controller = CmdLineController(player, cb_update_position)
        controller.run(initial_rate=self.manager.get_preferred_playback_rate(podcast),
                        initial_position=self.manager.get_last_position(episode))

        return cb_return_menu

    def update(self):
        print "Updating feeds..."
        self.podcasts = [get_podcast(link) for _, link in self.manager.links().iteritems()]
        print "All data retrieved"

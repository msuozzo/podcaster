from local import PodcastFileManager
from rss import feed_to_obj, parse_feed

from operator import attrgetter, itemgetter
from datetime import datetime


class FormatException(BaseException):
    pass


def get_menu_header(name, fill='-'):
    return [name, len(name) * fill]


def get_series(objs, name, getter, formatter=lambda f: f):
    header_row = [] if name is None else [name]
    return header_row + [formatter(getter(obj)) for obj in objs]


def get_command_series(num_objs):
    return ["CMD"] + map(str, range(1, num_objs + 1))


def pad_series(series, has_header, width=None, pad_char=' '):
    """Return the series arg with each element padded to the length of the
    longest element or `width` if it is provided.

    has_header - if True, the zeroeth element will be centered
    width - if provided, series will be padded to max(width, max_elem_length)
    pad_char - char with which to pad the series
    """
    padded_width = max(map(len, series)) if width is None else width
    first_func = str.center if has_header else str.ljust
    first = first_func(series[0], padded_width, pad_char)
    return [first] + [elem.ljust(padded_width, pad_char) for elem in series[1:]]

FIELD_PADDING = 1

def join_series(format_tuple, *args):
    """
    format_tuple - (fill_char, separation_char)
    """
    lens = map(len, args)
    if not all(l == lens[0] for l in lens):
        raise FormatException("Series not of equal length")
    num_rows = lens[0]
    if num_rows == 0:
        return ["  There's nothing here...."]
    char, sep = format_tuple
    padded_sep = sep.center(len(sep) + 2 * FIELD_PADDING, char)
    return [padded_sep.join(map(itemgetter(i), args)) for i in xrange(num_rows)]


def series_break(format_tuple, *args):
    widths = [len(arg[0]) for arg in args]
    char, sep = format_tuple
    padded_sep = sep.center(len(sep) + 2 * FIELD_PADDING, char)
    return padded_sep.join([char * width for width in widths])


def symmetric_header_footer(*series):
    #import pdb; pdb.set_trace()
    # Pad with header
    padded_series = [pad_series(s, True) for s in series]
    header_format = (' ', '|')
    series_format = (' ', ' ')
    top_break_format = ('-', 'v')
    bot_break_format = ('-', '^')
    # Format header
    ret = join_series(header_format, *[s[:1] for s in padded_series])
    ret.append(series_break(top_break_format, *padded_series))
    # Format series
    ret.extend(join_series(series_format, *[s[1:] for s in padded_series]))
    # Format footer
    ret.append(series_break(bot_break_format, *padded_series))
    return ret

PROMPT = "> "

def get_choice(valid_choices):
    choice = None
    while True:
        choice = raw_input(PROMPT)
        if choice not in valid_choices:
            print "Failed. Valid Commands: {%s}" % ", ".join(list(sorted(valid_choices)))
        else:
            return choice

class Podcaster(object):
    QUIT = -1
    def __init__(self):
        self.manager = PodcastFileManager()
        self.podcasts = []

    def run(self):
        current_menu = self.all_podcasts
        while current_menu != Podcaster.QUIT:
            current_menu = current_menu()
        self.manager.close()

    def all_podcasts(self):
        lines = get_menu_header('All Podcasts')
        commands = get_command_series(len(self.podcasts))
        updated = get_series(self.podcasts, "New?",
                                lambda f: f,
                                lambda field: "[%s]" % ("X" if self.manager.is_updated(field) else " "))
        names = get_series(self.podcasts, "Podcast",
                            attrgetter('name'))
        lines.extend(symmetric_header_footer(commands, updated, names))

        actions = {}
        for i, podcast in enumerate(self.podcasts):
            actions[str(i + 1)] = lambda p=podcast: self.one_podcast(p.name)

        more_actions = {
                ('a', 'Add a new podcast URL'): self.add_podcast,
                ('t', 'View Downloaded Episodes'): self.downloaded_podcasts
            }
        more_commands = get_series(sorted(more_actions.keys()), 'CMD',
                                    itemgetter(0))
        description = get_series(sorted(more_actions.keys()), 'Action',
                                    itemgetter(1))
        #FIXME: Previous lines may be shorter and will not be padded to this increased size
        padded_desc = pad_series(description, True, width=len(lines[0]))
        more_lines = symmetric_header_footer(more_commands, padded_desc)
        without_headers = more_lines[2:]
        lines.extend(without_headers)

        for (cmd, _), action in more_actions.iteritems():
            actions[cmd] = action

        print "\n".join(lines)

        choice = get_choice(actions.keys())
        return actions[choice]

    def one_podcast(self, name):
        #TODO
        return Podcaster.QUIT

    def add_podcast(self):
        #TODO
        return Podcaster.QUIT

    def downloaded_podcasts(self):
        #TODO
        return Podcaster.QUIT

    def play(self):
        #TODO
        return Podcaster.QUIT

    def update(self):
        print "Updating feeds..."
        self.podcasts = [feed_to_obj(parse_feed(link)) for link in self.manager.links().iteritems()]
        print "All data retrieved"


if __name__ == "__main__":
    Podcaster().run()

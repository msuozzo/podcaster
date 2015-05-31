"""Interface with RSS pages
"""
from http import get_meta_redirect, get_rss_link
from podcast import Podcast, Episode

from datetime import datetime

import feedparser


def _parse_feed(url):
    """Return feed structured via feedparser on success.
    None on failure
    """
    # first try to parse directly
    parsed_feed = feedparser.parse(url)

    # fall back to searching for an rss link
    if parsed_feed.bozo:
        #TODO: Generalize fallbacks
        # try to find an rss_link
        rss_link = get_rss_link(url)
        if rss_link is not None:
            return _parse_feed(rss_link)

        # try to find a redirect within the page
        redirect_url = get_meta_redirect(url)
        if redirect_url is not None:
            return _parse_feed(redirect_url)
        return None
    return parsed_feed if parsed_feed.feed else None


def _feed_to_obj(feed):
    """Converts a feedparser feed to a Podcast object
    """
    #TODO: use pytz to convert to UTC
    parse_datestr = lambda datestr: datetime.strptime(datestr, "%a, %d %b %Y %H:%M:%S %Z")
    episodes = []
    for entry in feed.entries:
        links = [link.href for link in entry.links if link.type.startswith('audio')]
        if not len(links):
            continue
        link = links[0]
        episode = Episode(link,
                            entry.get('title', ''),
                            entry.get('summary', ''),
                            parse_datestr(entry.published))
        episodes.append(episode)
    return Podcast(feed.href,
                    feed.feed.title,
                    feed.feed.get('author', ''),
                    feed.feed.get('link', ''),
                    feed.feed.get('summary', ''),
                    parse_datestr(feed.updated),
                    episodes)


def get_podcast(url):
    return _feed_to_obj(_parse_feed(url))


if __name__ == "__main__":
    import pprint

    hi_url = "http://feeds.podtrac.com/m2lTaLRx8AWb"
    shorten = lambda s: str(s)[:40] + ("..." if len(str(s)) > 40 else "")
    feed = _parse_feed(hi_url)
    for k, v in feed.iteritems():
        print k, shorten(v)
    print pprint.pprint(feed.feed)
    p = _feed_to_obj(feed)
    print repr(p)
    print pprint.pprint(feed.entries[0])

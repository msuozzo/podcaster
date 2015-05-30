"""Interface with RSS pages
"""
from http import get_meta_redirect, get_rss_link
from podcast import Podcast

from datetime import datetime

import feedparser



def parse_feed(url):
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
            return parse_feed(rss_link)

        # try to find a redirect within the page
        redirect_url = get_meta_redirect(url)
        if redirect_url is not None:
            return parse_feed(redirect_url)
        return None
    else:
        return parsed_feed


def feed_to_obj(feed):
    """Converts a feedparser feed to a Podcast object
    """
    episodes = []
    for entry in feed.entries:
        #TODO
        pass
    #TODO: use pytz to convert to UTC
    last_updated = datetime.strptime(feed.updated, "%a, %d %b %Y %H:%M:%S %Z")
    return Podcast(feed.href,
                    feed.feed.get('title', ''),
                    feed.feed.get('author', ''),
                    feed.feed.get('link', ''),
                    feed.feed.get('summary', ''),
                    last_updated)


if __name__ == "__main__":
    import pprint

    hi_url = "http://feeds.podtrac.com/m2lTaLRx8AWb"
    shorten = lambda s: str(s)[:40] + ("..." if len(str(s)) > 40 else "")
    feed = parse_feed(hi_url)
    for k, v in feed.iteritems():
        print k, shorten(v)
    print pprint.pprint(feed.feed)
    p = feed_to_obj(feed)
    print pprint.pprint(feed.entries[0])

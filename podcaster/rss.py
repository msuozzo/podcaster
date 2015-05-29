from podcaster.http import get_meta_redirect, get_rss_link

from datetime import datetime
import time

import feedparser


class Podcast(object):
    """A podcast feed
    """

    def __init__(self, url, **kwargs):
        self.url = url
        self.title = kwargs.get('title', self.url)
        self.author = kwargs.get('author', '')
        self.site_link = kwargs.get('link', '')
        self.description = kwargs.get('summary', '')

        #FIXME: choose good default for unmarked podcasts
        iso_updated = kwargs.get('updated_parsed', time.localtime())
        self.last_updated = datetime(*iso_updated[:7])

    def __str__(self):
        return '"%s" By %s' % (self.title, self.author)


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


if __name__ == "__main__":
    import pprint

    hi_url = "http://feeds.podtrac.com/m2lTaLRx8AWb"
    shorten = lambda s: str(s)[:40] + ("..." if len(str(s)) > 40 else "")
    feed = parse_feed(hi_url)
    for k, v in feed.iteritems():
        print k, shorten(v)
    print pprint.pprint(feed.feed)
    p = Podcast(feed.href, **feed.feed)

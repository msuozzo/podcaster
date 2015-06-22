"""Interface with RSS pages
"""
from podcaster.http import get_meta_redirect, get_rss_link

import feedparser
from dateutil import parser


def _parse_feed(url):
    """Return feed structured via feedparser on success.
    None on failure
    """
    if url is None:
        return
    # first try to parse directly
    parsed_feed = feedparser.parse(url)

    # fall back to searching for an rss link
    if parsed_feed.bozo:
        fallbacks = (get_rss_link, get_meta_redirect)
        for fallback in fallbacks:
            feed = _parse_feed(fallback(url))
            if feed is not None:
                return feed
        return
    return parsed_feed if parsed_feed.feed else None


def _podcast_data(feed):
    """Return podcast data from the feedparser feed `feed`
    """
    if feed is None:
        return None
    last_updated = parser.parse(feed.updated) if 'updated' in feed else \
                    parser.parse(feed.feed.updated) if 'updated' in feed.feed else \
                    None
    return (feed.feed.title, feed.href, last_updated,
                feed.feed.get('author', ''), feed.feed.get('link', ''),
                feed.feed.get('summary', ''))


def _episode_iter(feed):
    """Return an iterator over the episodes of the podcast contained in the
    feedparser feed `feed`
    """
    if feed is None:
        raise StopIteration()
    def has_audio_link(link_dict):
        """Return whether the link dictionary refers to an audio file
        """
        if 'type' in link_dict:
            return link_dict.type.startswith("audio")
        return link_dict.href.endswith("mp3")
    for entry in feed.entries:
        links = [link_dict.href for link_dict in entry.links if has_audio_link(link_dict)]
        if not len(links):
            continue
        yield (links[0], entry.get('title', ''), entry.get('summary', ''),
                parser.parse(entry.published))
    raise StopIteration()


def get_podcast(url):
    """Return a `Podcast` instance built from the feed retrieved from `url`

    url - the url of the feed to be processed
    """
    feed = _parse_feed(url)
    return (_podcast_data(feed), _episode_iter(feed))

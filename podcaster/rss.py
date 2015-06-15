"""Interface with RSS pages
"""
from podcaster.http import get_meta_redirect, get_rss_link
from podcaster.podcast import Podcast, Episode

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


def _feed_to_obj(feed):
    """Converts a feedparser feed to a Podcast object
    """
    if feed is None:
        return None
    def has_audio_link(link_dict):
        """Return whether the link dictionary refers to an audio file
        """
        if 'type' in link_dict:
            return link_dict.type.startswith("audio")
        return link_dict.href.endswith("mp3")
    episodes = []
    for entry in feed.entries:
        links = [link_dict.href for link_dict in entry.links if has_audio_link(link_dict)]
        if not len(links):
            continue
        link = links[0]
        episode = Episode(link,
                            entry.get('title', ''),
                            feed.feed.title,
                            entry.get('summary', ''),
                            parser.parse(entry.published))
        episodes.append(episode)
    if 'updated' in feed:
        last_updated = parser.parse(feed.updated)
    else:
        last_updated = parser.parse('1/1/1970 00:01:00+0000')
    return Podcast(feed.href,
                    feed.feed.title,
                    last_updated,
                    feed.feed.get('author', ''),
                    feed.feed.get('link', ''),
                    feed.feed.get('summary', ''),
                    episodes)


def get_podcast(url):
    """Return a `Podcast` instance built from the feed retrieved from `url`

    url - the url of the feed to be processed
    """
    return _feed_to_obj(_parse_feed(url))

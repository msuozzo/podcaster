"""Classes facilitating the storage of podcast data
"""
from pprint import pformat


class Podcast(object):
    """A podcast feed

    last_updated - If data is available, a datetime object representing the
                    last time the feed was modified, else None
    """
    def __init__(self, rss_url, name, author='', site_url='',
            description='', last_updated=None, episodes=None):
        self.rss_url = rss_url
        self.name = name
        self.author = author
        self.site_url = site_url
        self.description = description

        self.last_updated = last_updated
        self.rate = 1.0
        self.episodes = {episode.title: episode for episode in episodes} if episodes is not None else {}

    def to_simple_dict(self):
        """Return a dictionary of the data contained in this Podcast
        """
        return {
                "name": self.name,
                "description": self.description,
                "author": self.author,
                "site_url": self.site_url,
                "rss_url": self.rss_url,
                "last_updated": self.last_updated.isoformat(),
                "rate": self.rate,
                "episodes": {title: episode.to_simple_dict() for title, episode in self.episodes.iteritems()}}

    def __str__(self):
        return '"%s" By %s' % (self.name, self.author)

    def __repr__(self):
        """A pretty-printed representation of the podcast
        """
        return pformat(self.to_simple_dict())


class Episode(object):
    """A podcast episode
    """
    def __init__(self, url, title, podcast_name, description='', date_published=None):
        self.url = url
        self.title = title
        self.podcast_name = podcast_name
        self.description = description
        self.date_published = date_published

    def to_simple_dict(self):
        """Return a dictionary of the data contained in this Episode
        """
        #NOTE: podcast_name left out of dict (duplicated)
        return {
                "title": self.title,
                "url": self.url,
                "description": self.description,
                "date_published": self.date_published.isoformat()}

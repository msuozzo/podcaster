"""Classes facilitating the storage of podcast data
"""
from pprint import pprint


class Podcast(object):
    """A podcast feed

    last_updated - If data is unavailable, a datetime object representing the
                    last time the feed was modified, else None
    """
    def __init__(self, rss_url, name='', author='', site_url='',
            description='', last_updated=None, episodes=None):
        self.rss_url = rss_url
        self.name = name if name else rss_url
        self.author = author
        self.site_url = site_url
        self.description = description

        self.last_updated = last_updated
        self.rate = 1.0
        self.episodes = [] if episodes is None else episodes

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
                "episodes": map(Episode.to_simple_dict, self.episodes)}

    def __str__(self):
        return '"%s" By %s' % (self.name, self.author)

    def __repr__(self):
        """A pretty-printed representation of the podcast
        """
        return pprint(self.to_simple_dict())


class Episode(object):
    """A podcast episode

    local_copy - If a local copy exists, the path to the file, else None
    """
    def __init__(self, url, title, description='', date_published=None):
        self.url = url
        self.title = title
        self.description = description
        self.date_published = date_published
        self.local_copy = None
        self.last_position = None

    def to_simple_dict(self):
        """Return a dictionary of the data contained in this Episode
        """
        return {
                "title": self.title,
                "url": self.url,
                "description": self.description,
                "date_published": self.date_published.isoformat(),
                "local_copy": self.local_copy,
                "last_position": self.last_position}

    def deleted(self):
        """Clear object state of references to downloaded state
        """
        self.local_copy = None
        self.last_position = None

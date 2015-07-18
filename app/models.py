"""Flask data models
"""
from app import db

from datetime import datetime

from dateutil import parser as dateutil_parser
from dateutil.tz import tzutc


_EPOCH = dateutil_parser.parse('1/1/1970 00:01:00+0000')


class Podcast(db.Model):
    __tablename__ = 'podcasts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    rss_url = db.Column(db.String(2048))
    last_checked = db.Column(db.DateTime(timezone=True))
    last_updated = db.Column(db.DateTime(timezone=True))
    playback_rate = db.Column(db.Integer)
    episodes = db.relationship('Episode', order_by='Episode.date_published', cascade='all, delete, delete-orphan')

    def __init__(self, **kwargs):
        if 'last_updated' not in kwargs or kwargs['last_updated'] is None:
            kwargs['last_updated'] = datetime.now(tzutc())
        kwargs['last_checked'] = _EPOCH
        kwargs['playback_rate'] = 100
        db.Model.__init__(self, **kwargs)

    def check(self):
        self.last_checked = datetime.now(tzutc()).replace(tzinfo=None)

    def has_update(self):
        return self.last_checked < self.last_updated


class Episode(db.Model):
    __tablename__ = 'episodes'

    id = db.Column(db.Integer, primary_key=True)
    podcast_id = db.Column(db.Integer, db.ForeignKey('podcasts.id'))
    title = db.Column(db.String(128))
    url = db.Column(db.String(2047))
    date_published = db.Column(db.DateTime(timezone=True))
    last_position = db.Column(db.Integer, nullable=True)
    local_file = db.relationship('EpisodeFile', uselist=False)

    def __init__(self, **kwargs):
        kwargs['last_position'] = None
        kwargs['local_file'] = None
        db.Model.__init__(self, **kwargs)

    def is_downloaded(self):
        return self.local_file is not None

    def __str__(self):
        return 'Episode<podcast_id=%d, title=%s, published=%s>' % (self.podcast_id, self.title, self.date_published)


class EpisodeFile(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'))
    uri = db.Column(db.String(1024))
    date_created = db.Column(db.DateTime(timezone=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('date_created', datetime.now(tzutc()))
        db.Model.__init__(self, **kwargs)

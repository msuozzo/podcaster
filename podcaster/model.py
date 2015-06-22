"""
"""
from datetime import datetime

from dateutil import parser as dateutil_parser
from dateutil.tz import tzutc
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


BaseModel = declarative_base()


_EPOCH = dateutil_parser.parse('1/1/1970 00:01:00+0000')


class Podcast(BaseModel):
    """
    """
    __tablename__ = 'podcasts'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    rss_url = Column(String(2047))
    last_checked = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True))
    playback_rate = Column(Integer)
    episodes = relationship('Episode', order_by='Episode.id', cascade='all, delete, delete-orphan')

    def __init__(self, **kwargs):
        if 'last_updated' not in kwargs or kwargs['last_updated'] is None:
            kwargs['last_updated'] = datetime.now(tzutc())
        kwargs['last_checked'] = _EPOCH
        kwargs['playback_rate'] = 100
        BaseModel.__init__(self, **kwargs)

    def check(self):
        self.last_checked = datetime.now(tzutc()).replace(tzinfo=None)

    def has_update(self):
        return self.last_checked < self.last_updated


class Episode(BaseModel):
    """
    """
    __tablename__ = 'episodes'
    id = Column(Integer, primary_key=True)
    podcast_id = Column(Integer, ForeignKey('podcasts.id'))
    title = Column(String(128))
    url = Column(String(2047))
    date_published = Column(DateTime(timezone=True))
    last_position = Column(Integer, nullable=True)
    local_file = relationship('EpisodeFile', uselist=False)

    def __init__(self, **kwargs):
        kwargs['last_position'] = None
        kwargs['local_file'] = None
        BaseModel.__init__(self, **kwargs)

    def is_downloaded(self):
        return self.local_file is not None

    def __str__(self):
        return 'Episode<podcast_id=%d, title=%s, published=%s>' % (self.podcast_id, self.title, self.date_published)


class EpisodeFile(BaseModel):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey('episodes.id'))
    uri = Column(String(1024))
    date_created = Column(DateTime(timezone=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('date_created', datetime.now(tzutc()))
        BaseModel.__init__(self, **kwargs)

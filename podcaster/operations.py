"""
"""
from podcaster.model import Podcast, Episode, EpisodeFile, BaseModel
from podcaster.rss import get_podcast
from podcaster.store import SimplerFileStore
from podcaster.http import download_to_file, ConnectionError
from podcaster.view import ASCIIView

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import desc


class SessionError(Exception):
    pass


def _with_session(func):
    def with_session(self, *args, **kwargs):
        with self.session():
            return func(self, *args, **kwargs)
    return with_session


class Controller(object):
    def __init__(self, db_fname=None):
        db_path = 'sqlite://'
        if db_fname is not None:
            db_path = '/'.join((db_path, db_fname))
        self._engine = create_engine(db_path, echo=False)
        BaseModel.metadata.create_all(self._engine)
        self._session = None
        self.view = ASCIIView(self)
        self._store = SimplerFileStore('.podcasts')

    @contextmanager
    def session(self):
        """Context manager for 
        """
        new_session = self._session is None
        if new_session:
            self._session = sessionmaker(bind=self._engine)()
        yield self._session
        self._session.flush()
        if new_session:
            self._session.commit()
            self._session = None

    @staticmethod
    def _paginate(query, limit, offset=0):
        total = query.count()
        last_ind = offset + limit
        range_ = (offset, None if last_ind >= total else last_ind)
        return (query.limit(limit).offset(offset), range_)

    @_with_session
    def all_podcasts(self):
        podcasts = self._session.query(Podcast).order_by(Podcast.name)
        return self.view.all_podcasts(podcasts)

    @_with_session
    def episodes(self, podcast_id, base=0):
        podcast = self._session.query(Podcast).get(podcast_id)
        podcast.check()
        episode_query = self._session.query(Episode)\
                            .filter_by(podcast_id=podcast_id)\
                            .order_by(desc(Episode.date_published))
        episodes, page_range = Controller._paginate(episode_query, 10, base)
        return self.view.episodes(podcast, episodes, page_range)

    @_with_session
    def downloaded_episodes(self):
        episode_query = self._session.query(Episode, Podcast)\
                                    .filter(Episode.podcast_id == Podcast.id)\
                                    .join(EpisodeFile)\
                                    .order_by(desc(EpisodeFile.date_created))
        episodes = [episode for episode, _ in episode_query.all()]
        podcasts = [podcast for _, podcast in episode_query.all()]
        return self.view.downloaded_episodes(episodes, podcasts)

    @_with_session
    def update_podcasts(self, cb_return_menu):
        self.view.update()
        podcasts = self._session.query(Podcast).all()
        for podcast in podcasts:
            self._update_podcast(podcast)
        return cb_return_menu

    @_with_session
    def update_podcast(self, podcast_id, cb_return_menu):
        podcast = self._session.query(Podcast).get(podcast_id)
        self._update_podcast(podcast)
        return cb_return_menu

    def _update_podcast(self, podcast):
        podcast_tuple, episode_iter = get_podcast(podcast.rss_url)
        if podcast_tuple is None:
            raise Exception()
        _, _, last_updated, _, _, _ = podcast_tuple
        if last_updated is None or \
                last_updated.replace(tzinfo=None) <= podcast.last_updated:
            return
        podcast.last_updated = last_updated.replace(tzinfo=None)
        updated_ids = set([])
        episode_query = self._session.query(Episode).filter_by(podcast_id=podcast.id)
        for episode_tuple in episode_iter:
            url, title, _, published = episode_tuple
            episode = episode_query.filter_by(title=title, url=url,
                                                    date_published=published).scalar()
            if episode is None:
                episode = Episode(podcast_id=podcast.id, title=title, url=url,
                                        date_published=published)
                podcast.episodes.append(episode)
                # ensure episode is added to the db so it is assigned an ID
                self._session.flush()
            updated_ids.add(episode.id)
        absent_ids = episode_query.filter(~Episode.id.in_(updated_ids))
        for episode in absent_ids:
            self._session.delete(episode)

    def get_podcast_name(self, podcast_url):
        podcast_tuple, _ = get_podcast(podcast_url)
        if podcast_tuple is None:
            return None
        title, _, _, _, _, _ = podcast_tuple
        return title

    def add_podcast(self):
        return self.view.add_podcast()

    @_with_session
    def new_podcast(self, podcast_url):
        podcast_tuple, episode_iter = get_podcast(podcast_url)
        if podcast_tuple is None:
            return None
        title, rss_url, last_updated, _, _, _ = podcast_tuple
        podcast = Podcast(name=title, rss_url=rss_url, last_updated=last_updated)
        self._session.add(podcast)
        self._session.flush()
        for episode_tuple in reversed(list(episode_iter)):
            url, title, _, published = episode_tuple
            episode = Episode(podcast_id=podcast.id, title=title, url=url, date_published=published)
            podcast.episodes.append(episode)

    @_with_session
    def play(self, episode_id, cb_return_menu):
        episode = self._session.query(Episode).get(episode_id)
        podcast = self._session.query(Podcast).get(episode.podcast_id)
        if not episode.is_downloaded() and not self.view.download(episode):
            return cb_return_menu
        return self.view.play(podcast, episode, cb_return_menu)

    @_with_session
    def download_episode(self, episode_id, cb_progress=None):
        episode = self._session.query(Episode).get(episode_id)
        key = self._episode_key(episode_id)
        # Define callback closure to convert download callback format to progress format
        if cb_progress is not None:
            def cb_report(chunk_num, chunk_size, total_size):
                """Return the completion ratio of the download if available.
                Else, return None
                """
                if total_size != -1:
                    cb_progress((1. * chunk_size * chunk_num) / total_size)
                else:
                    cb_progress(None)
        else:
            cb_report = None
        # Attempt download
        try:
            local_fname, _ = download_to_file(episode.url, reporthook=cb_report)
        except ConnectionError:
            return False
        else:
            with open(local_fname, 'rb') as file_:
                self._store.put(key, file_)
            uri = 'file://' + self._store.get_path(key)
            episode.local_file = EpisodeFile(episode_id=episode_id, uri=uri)
            return True

    @_with_session
    def delete_episode(self, episode_id, cb_return_menu):
        episode = self._session.query(Episode).get(episode_id)
        key = self._episode_key(episode_id)
        self._store.remove(key)
        self._session.delete(episode.local_file)
        return cb_return_menu

    def update_episode_state(self, episode_id, position, playback_rate):
        episode = self._session.query(Episode).get(episode_id)
        podcast = self._session.query(Podcast).get(episode.podcast_id)
        episode.last_position = position
        podcast.playback_rate = playback_rate

    def _episode_key(self, episode_id):
        episode = self._session.query(Episode).get(episode_id)
        podcast = self._session.query(Podcast).get(episode.podcast_id)
        return ' - '.join((podcast.name, episode.title))

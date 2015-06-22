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
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc


class SessionError(Exception):
    pass


class Controller(object):
    def __init__(self):
        self._engine = create_engine('sqlite://', echo=False)
        BaseModel.metadata.create_all(self._engine)
        self._session = None
        self.view = ASCIIView(self)

    @contextmanager
    def session(self):
        """Context manager for 
        """
        new_session = self._session is None
        if new_session:
            self._session = sessionmaker(bind=self._engine)()
        yield self._session
        self._session.commit()
        if new_session:
            self._session = None

    def all_podcasts(self):
        with self.session() as session:
            podcasts = session.query(Podcast).order_by(Podcast.name)
            return self.view.all_podcasts(podcasts)

    def episodes(self, podcast_id, base=0):
        with self.session() as session:
            podcast = session.query(Podcast).filter_by(id=podcast_id).scalar()
            podcast.check()
            episode_query = session.query(Episode)\
                    .filter_by(podcast_id=podcast_id)\
                    .order_by(desc(Episode.date_published))
            total = episode_query.count()
            episodes = episode_query[base:base + 10]
            range_ = (base, None if base + 10 >= total else base + 10)
            return self.view.episodes(podcast, episodes, range_)

    def downloaded_episodes(self, base=0):
        with self.session() as session:
            local_episodes = session.query(Episode).filter(Episode.local_file.isnot(None)).order_by(Episode.local_file.date_created)
            total = local_episodes.count()
            episodes = local_episodes[base:base + 10]
            range_ = (None if base == 0 else base, None if base + 10 >= total else base + 10)
            return self.view.downloaded_episodes(episodes, range_)

    def print_episodes(self, podcast_id):
        with self.session() as session:
            podcast = session.query(Podcast).filter_by(id=podcast_id).scalar()
            for episode in podcast.episodes:
                print str(episode)

    def update_podcasts(self):
        self.view.update()
        with self.session() as session:
            rows = session.query(Podcast.id).all()
            for row in rows:
                self._update_podcast(row.id)


    def _update_podcast(self, podcast_id):
        if self._session is None:
            raise SessionError()
        podcast = self._session.query(Podcast).filter_by(id=podcast_id).scalar()
        podcast_tuple, episode_iter = get_podcast(podcast.rss_url)
        if podcast_tuple is None:
            raise Exception()
        _, _, last_updated, _, _, _ = podcast_tuple
        if last_updated is None:
            return
        if last_updated.replace(tzinfo=None) <= podcast.last_updated:
            return
        podcast.last_updated = last_updated.replace(tzinfo=None)
        updated_ids = set([])
        episode_query = self._session.query(Episode).filter_by(podcast_id=podcast.id)
        for episode_tuple in episode_iter:
            url, title, _, published = episode_tuple
            try:
                episode = episode_query.filter_by(title=title).scalar()
            except NoResultFound:
                episode = Episode(podcast_id=podcast.id, title=title, url=url,
                                    date_published=published)
                podcast.episodes.append(episode)
            else:
                episode.url = url
                episode.date_published = published.replace(tzinfo=None)
            self._session.flush()
            updated_ids.add(episode.id)
        absent_ids = episode_query.filter(~Episode.id.in_(updated_ids))
        for row in absent_ids:
            episode = episode_query.filter_by(id=row.id).scalar()
            self._session.delete(episode)


    def get_podcast_name(self, podcast_url):
        podcast_tuple, _ = get_podcast(podcast_url)
        if podcast_tuple is None:
            return None
        title, _, _, _, _, _ = podcast_tuple
        return title

    def add_podcast(self):
        return self.view.add_podcast()

    def new_podcast(self, podcast_url):
        with self.session() as session:
            podcast_tuple, episode_iter = get_podcast(podcast_url)
            if podcast_tuple is None:
                return None
            title, rss_url, last_updated, _, _, _ = podcast_tuple
            podcast = Podcast(name=title, rss_url=rss_url, last_updated=last_updated)
            session.add(podcast)
            session.flush()
            for episode_tuple in reversed(list(episode_iter)):
                url, title, _, published = episode_tuple
                episode = Episode(podcast_id=podcast.id, title=title, url=url, date_published=published)
                podcast.episodes.append(episode)

    def play(self, episode_id, cb_return_menu):
        with self.session() as session:
            episode = session.query(Episode).filter_by(id=episode_id).scalar()
            podcast = session.query(Podcast).filter_by(id=episode.podcast_id).scalar()
            if not episode.is_downloaded():
                if not self.view.download(episode):
                    return cb_return_menu
            return self.view.play(podcast, episode, cb_return_menu)


    def download_file(self, episode_id, cb_progress=None):
        #import pdb; pdb.set_trace()
        store = SimplerFileStore('.podcasts')
        with self.session() as session:
            episode = session.query(Episode).filter_by(id=episode_id).scalar()
            key = self._episode_key(episode_id, episode)
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
                    store.put(key, file_)
                uri = 'file://' + store.get_path(key)
                episode_file = EpisodeFile(episode_id=episode_id, uri=uri)
                episode.local_file = episode_file
        return True

    def delete_file(self, episode_id):
        store = SimplerFileStore('.podcasts')
        with self.session() as session:
            episode = session.query(Episode).filter_by(id=episode_id).scalar()
            key = self._episode_key(episode_id, episode)
            store.remove(key)
            session.delete(episode.local_file)

    def update_episode_state(self, episode_id, position, playback_rate):
        episode = self._session.query(Episode).filter_by(id=episode_id).scalar()
        podcast = self._session.query(Podcast).filter_by(id=episode.podcast_id).scalar()
        episode.last_position = position
        podcast.playback_rate = playback_rate

    def _episode_key(self, episode_id, episode=None, podcast=None):
        if self._session is None:
            raise SessionError()
        if episode is None:
            episode = self._session.query(Episode).filter_by(id=episode_id).scalar()
        if podcast is None:
            podcast = self._session.query(Podcast).filter_by(id=episode.podcast_id).scalar()
        return podcast.name + ' - ' + episode.title
from podcaster.model import Podcast, Episode, EpisodeFile, BaseModel
from podcaster.rss import get_podcast
from podcaster.store import SimplerFileStore
from podcaster.http import download_to_file, ConnectionError, ResponseError
from podcaster.view import ASCIIView

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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
        """Context manager for database session

        On enter: Create a new db session (provided one is not already in
            progress)
        On exit: Commit the session (provided one was created)
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
                            .order_by(Episode.date_published.desc())
        episodes, page_range = Controller._paginate(episode_query, 10, base)
        return self.view.episodes(podcast, episodes, page_range)

    @_with_session
    def downloaded_episodes(self):
        episode_query = self._session.query(Episode, Podcast)\
                                    .filter(Episode.podcast_id == Podcast.id)\
                                    .join(EpisodeFile)\
                                    .order_by(EpisodeFile.date_created.desc())
        episodes = [episode for episode, _ in episode_query.all()]
        podcasts = [podcast for _, podcast in episode_query.all()]
        return self.view.downloaded_episodes(episodes, podcasts)

    @_with_session
    def update_podcasts(self, cb_return_menu):
        self.view.update(start=True)
        podcasts = self._session.query(Podcast).all()
        for podcast in podcasts:
            try:
                self._update_podcast(podcast)
            except (ConnectionError, ResponseError) as err:
                self.view.update(error=(podcast, 'Failed to connect to update \
                    server (%s)' % str(err)))
        self.view.update(end=True)
        return cb_return_menu

    @_with_session
    def update_podcast(self, podcast_id, cb_return_menu):
        self.view.update(start=True)
        podcast = self._session.query(Podcast).get(podcast_id)
        try:
            self._update_podcast(podcast)
        except (ConnectionError, ResponseError) as err:
            self.view.update(error=(podcast, 'Failed to connect to update \
                server (%s)' % str(err)))
        self.view.update(end=True)
        return cb_return_menu

    def _update_podcast(self, podcast):
        podcast_tuple, episode_iter = get_podcast(podcast.rss_url)
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
        """Return the name of the podcast referred to by `podcast_url`

        Returns:
            On success: The name of the podcast
            On HTTP failure: A 2-tuple of the form (None, str_reason)
            On RSS failure: None
        """
        try:
            podcast_tuple, _ = get_podcast(podcast_url)
        except (ConnectionError, ResponseError) as err:
            return (None, str(err))
        if podcast_tuple is None:
            return None
        title, _, _, _, _, _ = podcast_tuple
        return title

    def add_podcast(self):
        """Dummy operation to transfer control to the view `add_podcast`
        """
        return self.view.add_podcast()

    @_with_session
    def new_podcast(self, podcast_url):
        """Add a new podcast

        Args:
            podcast_url: The url of the podcast RSS feed to add

        Returns:
            On success: None
            On failure: An error string
        """
        try:
            podcast_tuple, episode_iter = get_podcast(podcast_url)
        except (ConnectionError, ResponseError) as err:
            return str(err)
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
        """Play an episode

        Args:
            episode_id: The id of the episode to attempt to play
            cb_return_menu: The menu callback to invoked after the play
                operation is complete.
                NOTE: The operation is 'complete' when a triggered download
                fails, the user exits the player, or the episode finishes
                playback
        """
        episode = self._session.query(Episode).get(episode_id)
        podcast = self._session.query(Podcast).get(episode.podcast_id)
        if not episode.is_downloaded() and not self.view.download(episode):
            return cb_return_menu
        return self.view.play(podcast, episode, cb_return_menu)

    @_with_session
    def download_episode(self, episode_id, cb_progress=None):
        """Attempt to download an episode

        Args:
            episode_id: The id of the episode to be downloaded
            cb_progress: An optional callback function that will be called as
                frequently as possible with the completion ratio of the
                download.
                NOTE: If this information is not available, the callback will
                be called with `None`

        Return:
            On Success: None
            On Failure: An error string
        """
        episode = self._session.query(Episode).get(episode_id)
        key = self._episode_key(episode_id)
        # Define callback closure to convert download callback format to progress format
        if cb_progress is not None:
            def cb_report(chunk_num, chunk_size, total_size):
                """Call `cb_progress` with the completion ration if available.
                Else, call it with `None`
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
        except (ConnectionError, ResponseError) as err:
            return str(err)
        else:
            with open(local_fname, 'rb') as file_:
                self._store.put(key, file_)
            uri = 'file://' + self._store.get_path(key)
            episode.local_file = EpisodeFile(episode_id=episode_id, uri=uri)
            return None

    @_with_session
    def delete_episode(self, episode_id, cb_return_menu):
        """Delete an episode

        Args:
            episode_id: The id of the episode to be deleted
            cb_return_menu: The menu callback to be returned upon completion
                of the operation.
        """
        episode = self._session.query(Episode).get(episode_id)
        if episode.local_file is not None:
            key = self._episode_key(episode_id)
            self._store.remove(key)
            self._session.delete(episode.local_file)
        return cb_return_menu

    def update_episode_state(self, episode_id, position, playback_rate):
        episode = self._session.query(Episode).get(episode_id)
        podcast = self._session.query(Podcast).get(episode.podcast_id)
        episode.last_position = position
        podcast.playback_rate = playback_rate
        self._session.flush()

    def _episode_key(self, episode_id):
        """Return a (reasonably) unique string identifier for an episode

        Args:
            episode_id: The id of the episode for which the string identifier
                should be generated.
        """
        episode = self._session.query(Episode).get(episode_id)
        podcast = self._session.query(Podcast).get(episode.podcast_id)
        return ' - '.join((podcast.name, episode.title))

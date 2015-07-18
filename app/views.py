"""Flask Routes
"""
from app import app, db
from app.models import Podcast, Episode
from podcaster.rss import get_podcast

from flask import render_template, request


@app.teardown_request
def commit_database(exception=None):
    """Commit the current database session after each request
    """
    if exception is not None:
        raise exception  #pylint: disable=raising-bad-type
    db.session.commit()


@app.route('/all-podcasts')
@app.route('/')
def all_podcasts():
    """Display all podcasts
    """
    podcast_query = db.session.query(Podcast).order_by(Podcast.name)
    return render_template('all_podcasts.html', podcasts=podcast_query.all())


#TODO: Make more RESTful -> change to podcast url or name
@app.route('/podcast/<podcast_id>')
def episodes(podcast_id):
    """Display all episodes of the podcast with the id `podcast_id`
    """
    podcast = db.session.query(Podcast).get(podcast_id)
    #TODO: Pagination
    return render_template('episodes.html', podcast=podcast)


@app.route('/add-podcast')
def add_podcast():
    """Display an interface to add a podcast
    """
    error = None
    while True:
        url = request.values.get('feed-url', None)
        if url is None:
            break
        elif not url:
            error = 'URL must be provided'
            break
        podcast_tuple, episode_iter = get_podcast(url)
        if podcast_tuple is None:
            error = 'Failed to retrieve RSS feed'
            break
        if error is None:
            podcast_name = _add_podcast(podcast_tuple, episode_iter)
            return render_template('add.html', success=podcast_name)
    return render_template('add.html', error=error)


def _add_podcast(podcast_tuple, episode_iter):
    """Add the contents of a podcast feed to the database
    """
    name, rss_url, last_updated, _, _, _ = podcast_tuple
    podcast = Podcast(name=name, rss_url=rss_url, last_updated=last_updated)
    db.session.add(podcast)
    db.session.flush()
    for episode_tuple in reversed(list(episode_iter)):
        url, title, _, published = episode_tuple
        episode = Episode(podcast_id=podcast.id, title=title, url=url, date_published=published)
        podcast.episodes.append(episode)
    return name

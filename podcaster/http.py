"""Provide an interface for interaction with URLs and HTTP pages
"""
import socket
import urllib
import urllib2
from urlparse import urlparse

from bs4 import BeautifulSoup


class ConnectionError(Exception):
    """Indicate an error establishing a connection with a URL.
    This can include errors in the URL itself as well as those with the current
    internet connection.
    """
    pass


class ResponseError(Exception):
    """Indicate an HTTP error response
    """
    pass


def set_global_timeout(timeout=5):
    """Set the global timeout for the underlying sockets used by urllib

    Args:
        timeout: number of seconds after which the connection attempt should timeout
    """
    socket.setdefaulttimeout(timeout)


def download_to_file(url, fname, reporthook=None):
    """Wrapper around urllib.urlretrieve
    """
    try:
        urllib.urlretrieve(url, fname, reporthook)
    except IOError as err:
        raise ConnectionError('Failed to establish connection: %s' % err)


def default_to_http(url):
    """Return a URL that uses the HTTP scheme if none was provided
    """
    if not urlparse(url).scheme:
        return 'http://' + url
    return url


def test_connection():
    """Return whether
    """
    try:
        get_response('http://www.google.com')
    except (ResponseError, ConnectionError):
        return False
    else:
        return True


def get_response(url):
    """Return a file handle for the resource at `url`

    Args:
        url: the url identifying the resource that should be retrieved

    Raises:
        URLError: on basic connection errors
        ConnectionError: on HTTP errors
    """
    try:
        return urllib2.urlopen(url)
    except urllib2.HTTPError as http_err:
        raise ResponseError('Received HTTP Response %d from url %s: %s' %
                (http_err.code, http_err.geturl(), http_err.info()))
    except urllib2.URLError as url_err:
        raise ConnectionError('Failed to complete request: %s', url_err.reason)
    except ValueError as err:
        raise ConnectionError('Failed to complete request: %s', err)


def get_soup(url):
    """Return a BeautifulSoup instance for the contents of `url`
    """
    page = get_response(url)
    return BeautifulSoup(page.read(), 'lxml')


def _meta_redirect(soup):
    """If one exists, return the meta redirect url for the `soup` object.
    Else, return None.
    """
    meta = soup.find('meta', {'http-equiv': 'refresh'})
    return meta['content'].split('=')[1].strip() if meta else None


def get_meta_redirect(url):
    """If one exists, return the meta redirect url for the page at `url`.
    Else, return None.
    """
    try:
        soup = get_soup(url)
    except ResponseError:
        pass
    return _meta_redirect(soup) if soup is not None else None


def _rss_link(soup):
    """If one exists, return the RSS url for the `soup` object.
    Else, return None.
    """
    link = soup.find('link', {'type': 'application/rss+xml'})
    return link['href'] if link else None


def get_rss_link(url):
    """If one exists, return the RSS url for the page at `url`.
    Else, return None.
    """
    try:
        soup = get_soup(url)
    except ResponseError:
        pass
    return _rss_link(soup) if soup is not None else None


if socket.getdefaulttimeout() is None:
    set_global_timeout()

import urllib2

from bs4 import BeautifulSoup


def get_response(url):
    #TODO: throw Exception?
    try:
        return urllib2.urlopen(url)
    except urllib2.HTTPError:
        return None
    except urllib2.URLError:
        return None


def get_soup(url):
    page = get_response(url)
    return BeautifulSoup(page.read(), "lxml") if page is not None else None


def _meta_redirect(soup):
    meta = soup.find("meta", {"http-equiv": "refresh"})
    return meta["content"].split("=")[1].strip() if meta else None


def get_meta_redirect(url):
    soup = get_soup(url)
    return _meta_redirect(soup) if soup is not None else None


def _rss_link(soup):
    link = soup.find("link", {"type": "application/rss+xml"})
    return link["href"] if link else None


def get_rss_link(url):
    soup = get_soup(url)
    return _rss_link(soup) if soup is not None else None

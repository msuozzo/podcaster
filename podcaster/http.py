import urllib2

from bs4 import BeautifulSoup


def download_to_file(url, local_fname):
    #TODO: Add progressbar hook
    res = get_response(url)
    if res is None:
        return None
    with open(local_fname, 'wb') as local_file:
        local_file.write(res.read())
    return local_fname


def get_response(url):
    #TODO: throw Exception?
    try:
        return urllib2.urlopen(url)
    except urllib2.HTTPError:
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

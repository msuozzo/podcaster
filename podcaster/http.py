import urllib2

from bs4 import BeautifulSoup


def get_soup(url):
   #TODO: throw Exception?
   try:
      page = urllib2.urlopen(url)
   except urllib2.HTTPError:
      return None
   return BeautifulSoup(page.read(), "lxml")


def _meta_redirect(soup):
   meta = soup.find("meta", {"http-equiv": "refresh"})
   return meta["content"].split("=")[1].strip() if meta else None


def get_meta_redirect(url):
   soup = get_soup(url)
   if soup is None:
      return None
   return _meta_redirect(soup)


def _rss_link(soup):
   link = soup.find("link", {"type": "application/rss+xml"})
   return link["href"] if link else None


def get_rss_link(url):
   soup = get_soup(url)
   if soup is None:
      return None
   return _rss_link(soup)

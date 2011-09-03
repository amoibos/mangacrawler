#!/usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2 Clauses BSD

from os import mkdir
from os.path import join, exists
from sys import exit, argv, stderr
from shutil import move
import thread
from urlparse import urljoin

import html5lib
import mechanize
import BeautifulSoup

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2011, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.2"

class Sites(object):
    def __init__(self):
        self._finished = 0

# sample url: http://www.mangafox.com/manga/a_girls/?no_warning=1
# tested on 09/2011
class MangaFox(Sites):
    def __init__(self, url):
        Sites.__init__(self)
        # html5 parser engine
        beautifulSoup = html5lib.HTMLParser(
            tree=html5lib.treebuilders.getTreeBuilder("beautifulsoup"))
        # browser engine
        browser = mechanize.Browser()
        # no special header needed, yet
        browser.add_headers = []
        soup = beautifulSoup.parse(browser.open(url))
        # get all chapters of this manga
        pages = self._get_pages(soup, url)
        amount_threads = len(pages)
        # start for every chapter a thread
        for page in pages:
            thread.start_new_thread(self.download, (page, url))
        # good enough, run until all threads done
        while self._finished < amount_threads:
            pass

    def download(self, page, url):
        beautifulSoup = html5lib.HTMLParser(
            tree=html5lib.treebuilders.getTreeBuilder("beautifulsoup"))
        browser = mechanize.Browser()
        browser.add_headers = []
        soup = beautifulSoup.parse(browser.open(url))
        # create directory hierachy
        full_path = ""
        for parts in page[1:]:
            full_path = join(full_path, parts)
            if not exists(full_path):
                mkdir(full_path)
            
        # my anchor is the chapter overview site
        anchor = beautifulSoup.parse(browser.open(page[0]))
        # get all links to the images
        for entry in anchor.find("select", {"class":"middle"}).findAll("option"):
            url = page[0]
            site = "%s/%s%s" % (url[:url.rfind("/")], entry["value"], url[url.rfind(".htm"):])
            soup = beautifulSoup.parse(browser.open(site))
            # get the absolute link to image
            image_page = soup.find("img", {"id":"image"})
            url = image_page["src"]
            # get image and save it(in temp directory)
            file_path = browser.retrieve(url)[0]
            # move to right directory
            move(file_path, join(full_path, url.split("/")[-1]))
        self._finished += 1
        
    def _get_pages(self, soup, url):
        pages = []
        url_str = url[:url.find(".com") + len(".com")]
        link_list = soup.findAll("a", attrs={"class":"ch"})
        for link in link_list:
            # split into '', "manga", TITLE, volume, chapter, html file 
            parts = link['href'].split('/')
            chapter_url = urljoin(url_str, link['href'])
            pages.append([str(chapter_url), str(parts[2]), str(parts[3]), str(parts[4])])
        return pages


def main(url):
    if "mangafox" in url:
        MangaFox(url)
    
if __name__ == "__main__":
    if len(argv) > 1:
        main(argv[1])
    else:
        print >> stderr, "arguments: <URL>"
        exit(-1)
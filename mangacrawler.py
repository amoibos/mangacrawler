#!/usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2 Clauses BSD

from os import mkdir
from os.path import join, exists
from sys import exit, argv, stderr
from shutil import move
import thread
from urlparse import urljoin, urlsplit

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
        self._running = 0
        self.MAX_THREAD = 1

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
        # start for every chapter a thread
        self._finished = len(pages)
        for page in pages:
            while self._running > self.MAX_THREAD:
                pass
            thread.start_new_thread(self.download, (page, url))
        # good enough, run until all threads done
        while self._finished:
            pass

    def download(self, page, url):
        self._running += 1
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
        no = 0
        for entry in anchor.find("select", {"class":"middle"}).findAll("option"):
            url = page[0]
            site = "%s/%s%s" % (url[:url.rfind("/")], entry["value"], url[url.rfind(".htm"):])
            soup = beautifulSoup.parse(browser.open(site))
            # get the absolute link to image
            image_page = soup.find("img", {"id":"image"})
            url = image_page["src"]
            # get image and save it(in temp directory)
            file_path = browser.retrieve(url)[0]
            no += 1
            img_name = "%04d%s" % (no, file_path[file_path.rfind("."):])
            # move to right directory
            move(file_path, join(full_path, img_name))
        self._finished -= 1
        self._running -= 1
        
    def _get_pages(self, soup, url):
        pages = []
        url_str = urlsplit(url)[1]
        link_list = soup.findAll("a", attrs={"class":"ch"})
        for link in link_list:
            # split into '', "manga", TITLE, volume, chapter, html file 
            parts = link['href'].split('/')
            chapter_url = urljoin(url_str, link['href'])
            pages.append([str(chapter_url), str(parts[2]), str(parts[3]), str(parts[4])])
        return pages

# http://www.mangareader.net/163/sekirei.html
# tested 09/2011
class MangaReader(Sites):
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
        # start for every chapter a thread
        self._finished = len(pages)
        for page in pages:
            while self._running > self.MAX_THREAD:
                pass
            thread.start_new_thread(self.download, (page, url))
        # good enough, run until all threads done
        while self._finished:
            pass


    def download(self, page, url):
        self._running += 1
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
        no = 0
        # get all links to the images
        for entry in anchor.find("select", {"id":"pageMenu"}).findAll("option"):
            url = page[0]
            site = urljoin(url, entry["value"])
            soup = beautifulSoup.parse(browser.open(site))
            # get the absolute link to image
            image_page = soup.find("img", {"id":"img"})
            url = image_page["src"]
            no += 1
            # get image and save it(in temp directory)
            file_path = browser.retrieve(url)[0]
            img_name = "%04d%s" % (no, file_path[file_path.rfind("."):])
            # move to right directory
            move(file_path, join(full_path, img_name))
        self._finished -= 1
        self._running -= 1
        
    def _get_pages(self, soup, url):
        pages = []
        url_str = urlsplit(url)[1]
        table = soup.find("table", attrs={"id":"listing"})
        link_list = table.findAll("a")
        chapter = 0
        name = urlsplit(url)[2].split("/")[-1]
        title = name[:name.rfind(".htm")]
        for link in link_list:
            chapter_url = urljoin(url_str, link['href'])
            chapter += 1
            pages.append([str(chapter_url), str(title), str("%s" % chapter)])
        return pages

def main(url):
    if "mangafox" in url:
        print "mangafox site detected"
        MangaFox(url)
    elif "mangareader" in url:
        print "mangareader site detected"
        MangaReader(url)
    else:
        print >> stderr, "no site detected"
    
if __name__ == "__main__":
    if len(argv) > 1:
        main(argv[1])
    else:
        print >> stderr, "arguments: <URL>"
        exit(-1)
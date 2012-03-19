#!/usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2 Clauses BSD

from os import mkdir
from os.path import join, exists
from sys import exit, argv, stderr
from shutil import move
from urlparse import urljoin, urlsplit
from multiprocessing import Process, Queue
from Queue import Empty

import html5lib
import mechanize
import BeautifulSoup


__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2012, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.3"

class Sites(object):
    def __init__(self, url):
        self._dict = {}
        self.run(url)
    
    def _components(self, url):
        # html5 parser engine
        beautifulSoup = html5lib.HTMLParser(
            tree=html5lib.treebuilders.getTreeBuilder("beautifulsoup"))
        # browser engine
        browser = mechanize.Browser()
        browser.addheaders = [('User-agent', 
        'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        soup = beautifulSoup.parse(browser.open(url))
        return beautifulSoup, browser, soup

    def run(self, url):
        beautifulSoup, browser, soup = self._components(url)
        # get all chapters of this manga
        pages = self._get_pages(soup, url)
        work_queue = Queue()
        for element in pages:
            work_queue.put(element)
        
        # create directories and start tasks(processes)
        for page in pages:
            self._create_dir(page)
        processes = [Process(target=self._do_work, args=(work_queue, url,)) for i in range(8)]
        for p in processes:
            p.start()
        for p in processes:
            p.join()
    
    def _do_work(self, work_queue, url):
        while True:
            try:
                self.download(work_queue.get(block=False), url)
            except Empty:
                break

    def _create_dir(self, page):
        full_path = ""
        for part in page[1:]:
            full_path = join(full_path, part)
            if not exists(full_path):
                mkdir(full_path)
        self._dict["".join(page[1:])] = full_path

# sample url: http://www.mangafox.com/manga/a_girls/?no_warning=1
# tested on 09/2011
class MangaFox(Sites):
    def __init__(self, url):
        Sites.__init__(self, url)
        
    def download(self, page, url):
        beautifulSoup, browser, soup = self._components(url)
        full_path = self._dict["".join(page[1:])]
            
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

# sample url: http://www.meinmanga.com/manga/Berserk/kapitel/Bd_1_Der_Schwarze_Ritter/
# tested 03/2012
class MeinManga(Sites):
    def __init__(self, url):
        Sites.__init__(self, url)
   
    def download(self, page, url):
        beautifulSoup, browser, soup = self._components(url)
        full_path = self._dict["".join(page[1:])]
            
        # my anchor is the chapter overview site
        anchor = beautifulSoup.parse(browser.open(page[0]))
        # get all links to the images
        no = 0
        for entry in anchor.findAll("select")[1].findAll("option"):
            url = page[0]
            site = "%s%s%s" % (url, entry["value"], ".html")
            soup = beautifulSoup.parse(browser.open(site))
            # get the absolute link to image
            image_page = soup.findAll("img", {"class":"pic_fragment"})
            if image_page == None:
                image_page = soup.find("img", {"class":"pic_fragment_biggest"})
            # some sites have splitted images
            appendix = ['a','b','c','d']
            part = 0
            for fragment in image_page:
                file_path = browser.retrieve(image_page[part]["src"])[0]
                if part == 0:
                    no += 1
                img_name = "%04d%s%s" % (no, appendix[part], file_path[file_path.rfind("."):])
                # move to right directory
                move(file_path, join(full_path, img_name))
                part += 1
                
    def _get_pages(self, soup, url):
        pages = []
        div_element = soup.find("div", {"id":"content"})
        select_element = soup.find("select")
        chapters = select_element.findAll("option")
        
        for chapter in chapters:
            # "http:", '', "www.meinmanga.com", "manga", TITLE, "kapitel", titel, ''
            parts = chapter['value'].split('/')
            pages.append([chapter['value'], str(parts[4]), str(parts[-2]), ""])
        return pages

# sample url: http://www.mangareader.net/163/sekirei.html
# tested 09/2011
class MangaReader(Sites):
    def __init__(self, url):
        Sites.__init__(self, url)

    def download(self, page, url):
        beautifulSoup, browser, soup = self._components(url)
        full_path = self._dict["".join(page[1:])]
            
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
    elif "meinmanga" in url:
        print "meinmanga site detected"
        MeinManga(url)
    else:
        print >> stderr, "no site detected"
    
if __name__ == "__main__":
    if len(argv) > 1:
        main(argv[1])
    else:
        print >> stderr, "arguments: <URL>"
        exit(-1)
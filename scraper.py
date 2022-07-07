# -*- coding: utf-8 -*-

import re
from urllib.parse import urlparse
from urllib.parse import urljoin

from bs4 import BeautifulSoup 
from bs4.element import Comment

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from utils import get_logger
import logging
import settings


# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
# https://www.dataquest.io/blog/web-scraping-python-using-beautiful-soup/
# http://www.compjour.org/warmups/govt-text-releases/intro-to-bs4-lxml-parsing-wh-press-briefings/

# NOTES: Using </a> html tag, you can get a list of hyperlinks that are on the page. Also calling on 'href' pulls up the link that is tied
# EXAMPLE: <a class="sister" href="http://example.com/tillie" id="link3">
# SAMPLE CODE to get hyperlinks using </a> tag and pull using the href:
#     for link in soup.find_all('a'):
#     print(link.get('href'))
# http://example.com/elsie
# http://example.com/lacie
# http://example.com/tillie


def scraper(url, resp):
    global loggr
    loggr = get_logger("URL_DATA")
    if is_valid(url) == False:
        return[]
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    pages = {}
    maxWord = 0 # Keeping track of maximum word count
    longestPage = "" # Keep track of the url that has the highest word count    
    # check if valid url
    urlList = list()
    urlSet = set()  # keeps track of unique sites

    # check if page is in urlSet
    # before adding urls to list, add to urlSet after making it just the domain and path (e.g. 'https//domain/path')
    url = url.split('?')[0]
    url = url.split('#')[0]
    tempURL = urlparse(url)  # parse the url in question
    tempURL_path = tempURL.path  # get the path of the url
    tempURL_domain = tempURL.netloc  # get the domain of the url

    # checks if subdomain of ics.uci.edu, updates dictionary if so
    if ".ics.uci.edu" in tempURL.netloc:
        if tempURL.netloc in settings.subdomains.keys():
            settings.subdomains[tempURL.netloc] += 1
        else:
            settings.subdomains[tempURL.netloc] = 1
    
    combinedURL = tempURL_domain + tempURL_path  # string concatenation of the domain and the path
    
    try:
    
        s = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)  # credit to: https://stackoverflow.com/questions/23013220/max-retries-exceeded-with-url-in-requests
        a = requests.adapters.HTTPAdapter(max_retries=retry)  # ^ used to pause the program if accessing too many files
        a.DEFAULT_RETRIES = 5
        
        s.mount('http://', a)
        s.mount('https://', a)
        page = s.get(url)  # put into the queue

        soup = BeautifulSoup(page.content, 'html.parser')  # parsing the page [getting the content of the page]

        # if (combinedURL not in urlSet):  # if it is not in the set already
        #     urlSet.add(combinedURL)  # put the string into the set, into a set since there cannot be duplicates

        # check if page is a low information value page (gotta determine how we want to define that)

        # if good, search webpage for other urls to add to queue w/ beautiful soup
        for link in soup.find_all('a'):
            temp = link.get('href')
            if temp != None:
                temp = temp.split('?')[0]
                temp = temp.split('#')[0]
            urlList.append(temp)

        text = page.text
        soup = BeautifulSoup(text)
        words = [url, 0]

        # list of English stopwords
        stopWords = [
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few",
        "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
        "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
        "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd",
        "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these",
        "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we're", "we've",
        "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't",
        "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
        ]

        # finds visible tokens in the webpage and saves statistics for analysis (number of each token, total number of tokens)
        [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]  # adapted from: https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
        visible_text = soup.getText()
        wordsContent = visible_text.lower().split()
        for word in wordsContent:
            tokens = re.findall("[a-z|A-Z|-|']+", word.lower(), flags=re.IGNORECASE) # list of visible tokens in the webpage
            for i in tokens:
                wrd = i.encode('utf-8')
                words[1] += 1
                
                
                if (wrd not in stopWords):  # only adds word if word is not considered an English stop word
                    if (wrd not in settings.wordsDict.keys()):
                        settings.wordsDict[wrd] = 1
                    else:
                        settings.wordsDict[wrd] += 1

        settings.uniqueURLs.add(url)  # adds URL to the set of all unique URLs enc
        settings.wordsList.append(words)  # list of lists, wordsList[x][0] = url, [1] = # of words
        settings.writeToFile()
        
        # closes connection
        s.close()
        page.close()
    except:
        print()

    return urlList


def is_valid(url):
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in set(["http", "https"]):
            return False

        # scheme://netloc/path;parameters?query#fragment
        # https://docs.python.org/3/library/urllib.parse.html

        # check if valid domain to visit
        if (not re.search(
                r"/*\.(ics.uci.edu|cs.uci.edu|informatics.uci.edu|stat.uci.edu)$", parsed.netloc.lower())
        ):
            return False
            # check if in valid domains: ()
            # *.ics.uci.edu/*
            # *.cs.uci.edu/*
            # *.informatics.uci.edu/*
            # *.stat.uci.edu/*

        # check if either physics or economics domain
        if (re.search(r"/*\.(physics.uci.edu|economics.uci.edu)$", parsed.netloc.lower())):
            return False
        
        # checks if it contains some blacklisted phrases that often cause errors or are low information pages
        if (re.search(r"/*\.(events)$", parsed.path.lower())):
            return False
        
        if (re.search(r"/*\.(evoke)$", parsed.path.lower())):
            return False

        if (re.search(r"/*\.(calendar)$", parsed.path.lower())):
            return False

        if "~shantas/publications" in parsed.path.lower():
            return False

        # checks if the url path includes blacklisted strings/file extensions that trap the crawler
        netlocs = ["ftp", "password"]
        extens = ["pdf", "css", "exe", "hyperware", "download"]
        givenExtens = ["css", "js", "bmp", "gif", "jpeg", "ico", 
                     "png", "tiff", "mid", "mp2", "mp3", "mp4", 
                     "wav", "avi", "mov", "mpeg", "ram", "m4v", "mkv", "ogg", "ogv", "pdf", 
                     "ps", "eps", "tex", "ppt", "pptx", "doc", "docx", "xls", "xlsx", "names", 
                     "data", "dat", "exe", "bz2", "tar", "msi", "bin", "7z", "psd", "dmg", "iso",
                     "epub", "dll", "cnf", "tgz", "sha1", "php",
                     "thmx", "mso", "arff", "rtf", "jar", "csv", 
                     "rm", "smil", "wmv", "swf", "wma", "zip", "rar", "gz"
                    ]

        for netl in netlocs:
            if netl in parsed.netloc.lower():
                return False

        for ext in givenExtens: 
            if ext in parsed.path.lower():
                return False
            if ext in parsed.query.lower():
                return False

        for ext in extens:
            if ext in parsed.path.lower():
                return False
            if ext in parsed.query.lower():
                return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        
    except TypeError:
        print("TypeError for ", parsed)
        raise

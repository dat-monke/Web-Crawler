# settings.py

def init():
    global wordsList
    global wordsDict
    global uniqueURLs
    global subdomains
    wordsList = []  # tracks all words count in urls
    wordsDict = {}  # tracks unique words
    uniqueURLs = set()  # tracks unique URLs crawled
    subdomains = {}  # track of unique subdomains of ics.uci.edu

def writeToFile():
    f = open("reportData.txt", 'w')
    f.write("Words list:\n")
    f.write(str(wordsList))
    f.close()

    f = open("reportData.txt", 'a')
    f.write("Words dictionary:\n")
    f.write(str(wordsDict))
    f.close()

    f = open("reportData.txt", 'a')
    f.write("Unique URLs:\n")
    f.write(str(uniqueURLs))
    f.close()

    f = open("reportData.txt", 'a')
    f.write("Subdomains:\n")
    f.write(str(subdomains))
    f.close()
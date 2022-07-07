from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper
import settings
import time
import pprint


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.urlLog = get_logger("URL DATA")
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            while resp.status not in range(200, 399) or resp.status == 204:
                self.frontier.mark_url_complete(tbd_url)
                tbd_url = self.frontier.get_tbd_url()
                if not tbd_url:
                    self.logger.info("Frontier is empty. Stopping Crawler.")
                    break
                resp = download(tbd_url, self.config, self.logger)
            if not tbd_url:
                break
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper(tbd_url, resp)
            self.urlLog.info("Unique URLs: %s" % str(len(settings.uniqueURLs)))
            niceDict = pprint.pformat(settings.subdomains)
            self.urlLog.info("ics.uci.edu subdomains: %s" % str(niceDict))
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
    

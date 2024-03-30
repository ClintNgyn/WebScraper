import requests
from time import time
from bs4 import BeautifulSoup

from .exceptions import FetchError
from requests.exceptions import RequestException


class WebScraper:
    def __init__(self, base_url, *paths):
        self.base_url = base_url
        self.paths = paths
        self.soups = dict()
        self.last_fetch_time = 0

    def fetch_all(self) -> dict:
        """
        Scrapes all pages provided in self.paths
        Caches result in self.soups (only re-fetches data every 120s)
        """

        current_time = time()

        if not self.soups or (current_time - self.last_fetch_time >= 120):
            print("-> fetching")
            self.soups = dict()
            for path in self.paths:
                url = self.base_url + path
                try:
                    res = requests.get(url)
                    res.raise_for_status()
                    self.soups[path] = BeautifulSoup(res.content, "html.parser")

                except RequestException as req_ex:
                    raise FetchError(f'Failed to fetch "{url}": \n    -> {req_ex}')

            self.last_fetch_time = current_time

        print("-> cached")
        return self.soups

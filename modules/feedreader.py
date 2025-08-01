from functools import cache
from threading import Timer
from time import strftime

import feedparser
import requests
from pandas import DataFrame
from requests.exceptions import ConnectionError

from containers import TableModule


# noinspection PyPep8Naming
class FeedReader(TableModule):
    justify = {'index': 'right'}
    humanize = {
        'index'           : lambda i: str(i) + '.',
        'published_parsed': lambda t: strftime("%b %d", t)
    }
    colorize = {
        'published_parsed': lambda t: f"[yellow]{t}[/yellow]",
        'source'          : lambda t: f"[green]{t}[/green]"
    }

    __cache = {}

    def __init__(self, *, feeds: list[str], showSource=True, showPublishDate=True, showIndex=False, limit=20, **kwargs):
        columns = []
        if showIndex:
            columns.append('index')
        if showSource:
            columns.append('source')
        if showPublishDate:
            columns.append('published_parsed')
        columns.append('title')

        super().__init__(columns=columns, show_header=False, feeds=feeds, showSource=showSource,
                         showPublishDate=showPublishDate, showIndex=showIndex, limit=limit, **kwargs)

        self.feeds = feeds
        self.limit = limit

    @cache
    def cache_redirects(self, url):
        newurl = requests.head(url, allow_redirects=True).url
        if newurl != url:
            self.logger.info('Caching redirection for {} to {}', url, newurl)
        return newurl

    def get_feed(self, feed_url):
        try:
            self.logger.debug("Getting feed from {}", feed_url)
            feed = feedparser.parse(self.cache_redirects(feed_url))
            self.logger.debug("Feed request returned {}", feed.status)
            if feed.status == 200:
                for entry in feed.entries:
                    entry['source'] = feed.feed.title

                self.__cache[feed_url] = feed.entries
                return feed.entries
            elif feed.status == 429:
                # Slow down requests if HTTP 429 Too Many Requests is being returned
                # Next request will be sent after number of seconds specified in 
                # header 'Retry-After' or 60 seconds if absent.
                try:
                    sleep_time = int(feed.headers.get('retry-after', '60'))
                except KeyError | ValueError:
                    sleep_time = 60

                self.logger.warning("{} returned status 429, waiting {} seconds before retrying", feed_url, sleep_time)

                def retry():
                    self.get_feed(feed_url)
                    self.update(fetch_updates=False)

                Timer(sleep_time + 1, retry).start()
            else:
                self.notify(f"Failed to get RSS feed {feed_url}. Status code: {feed.status}", severity="warning")
        except ConnectionError:
            self.notify(f"Failed to get RSS feed {feed_url}. Connection error", severity="warning")
        return self.__cache.get(feed_url, [])

    def get_fresh_news(self):
        return [entry for feed_url in self.feeds for entry in self.get_feed(feed_url)]

    def get_news_from_cache(self):
        return [entry for feed_url in self.feeds for entry in self.__cache.get(feed_url, [])]

    def __call__(self, fetch_updates=True):
        if fetch_updates:
            news = self.get_fresh_news()
        else:
            news = self.get_news_from_cache()

        df = DataFrame.from_records(news)
        if df.empty:
            return None

        df = df.sort_values('published_parsed', ascending=False).reset_index()
        del df['index']
        df.reset_index(inplace=True)
        df['index'] += 1

        return df.head(self.limit)


widget = FeedReader

from functools import cache
from time import strftime

import feedparser
from loguru import logger
from pandas import DataFrame
import requests
from requests.exceptions import ConnectionError

from containers import TableModule


class FeedReader(TableModule):
    justify={'index': 'right'}
    humanize={
        'index': lambda i: str(i)+'.',
        'published_parsed': lambda t: strftime("%b %d", t)
    }
    colorize={
        'published_parsed': lambda t: f"[yellow]{t}[/yellow]",
        'source': lambda t: f"[green]{t}[/green]"
    }
    
    __cache = {}
    
    def __init__(self, *, feeds:list[str], showSource=True, showPublishDate=True, showIndex=False, limit=20, **kwargs):
        columns = []
        if showIndex:
            columns.append('index')
        if showSource:
            columns.append('source')
        if showPublishDate:
            columns.append('published_parsed')
        columns.append('title')
    
        super().__init__(columns=columns, show_header=False, **kwargs)          
            
        self.feeds=feeds
        self.limit=limit
        
    @cache
    def cache_redirects(self, url):
        newurl = requests.head(url, allow_redirects=True).url
        if newurl != url:
            logger.info('Caching redirection for {} to {}', url, newurl)
        return newurl
        
    def __call__(self):
        news = []
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(self.cache_redirects(feed_url))
                if feed.status == 200:
                    for entry in feed.entries:
                        entry['source']=feed.feed.title

                    self.__cache[feed_url] = feed.entries
                    news.extend(feed.entries)
                else:
                    self.notify(f"Failed to get RSS feed {feed.url}. Status code: {feed.status}", severity="warning")
                    news.extend(self.__cache.get(feed_url, []))
            except ConnectionError:
                self.notify(f"Failed to get RSS feed {feed.url}. Connection error", severity="warning")
                news.extend(self.__cache.get(feed_url, []))
        
        df = DataFrame.from_dict(news).sort_values('published_parsed', ascending=False).reset_index()
        del df['index']
        df.reset_index(inplace=True)
        df['index'] += 1
        
        return df.head(self.limit)

    
widget = FeedReader
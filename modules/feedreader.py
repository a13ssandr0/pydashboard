from time import strftime

import feedparser
from pandas import DataFrame
from requests.exceptions import ConnectionError

from basemod import TableModule


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
        self.feeds=feeds
        
        columns = []
        if showIndex:
            columns.append('index')
        if showSource:
            columns.append('source')
        if showPublishDate:
            columns.append('published_parsed')
        columns.append('title')
            
        self.limit=limit
        super().__init__(columns=columns, show_header=False, **kwargs)          
        
    def __call__(self):
        news = []
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                if feed.status == 200:
                    for entry in feed.entries:
                        entry['source']=feed.feed.title
                        # news.append(entry)
                    self.__cache[feed_url] = feed.entries
                    news.extend(feed.entries)
                else:
                    self.notify(f"Failed to get RSS feed {feed.url}. Status code: {feed.status}", severity="warning")
                    news.extend(self.__cache[feed_url])
            except ConnectionError:
                self.notify(f"Failed to get RSS feed {feed.url}. Connection error", severity="warning")
                news.extend(self.__cache[feed_url])
        
        df = DataFrame.from_dict(news).sort_values('published_parsed', ascending=False).reset_index()
        del df['index']
        df.reset_index(inplace=True)
        df['index'] += 1
        
        return df.head(self.limit)

    
widget = FeedReader
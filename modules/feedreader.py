from time import strftime

import feedparser
from pandas import DataFrame

from basemod import BaseModule
from helpers.strings import rjust
from helpers.tables import mktable


class FeedReader(BaseModule):
    def __init__(self, *, feeds:list[str], showSource=True, showPublishDate=True, showIndex=False, limit=20, **kwargs):
        self.feeds=feeds
        
        self.columns = []
        if showIndex:
            self.columns.append('index')
        if showSource:
            self.columns.append('source')
        if showPublishDate:
            self.columns.append('published_parsed')
        self.columns.append('title')
            
        self.limit=limit
        super().__init__(**kwargs)          
        
    def __call__(self):
        news = []
        for feed in self.feeds:
            feed = feedparser.parse(feed)
            if feed.status == 200:
                for entry in feed.entries:
                    entry['source']=feed.feed.title
                    news.append(entry)
            else:
                return f"Failed to get RSS feed {feed.url}. Status code: {feed.status}"
                
        
        df = DataFrame.from_dict(news).sort_values('published_parsed', ascending=False).reset_index()
        del df['index']
        df.reset_index(inplace=True)
        df['index'] += 1
        
        return mktable(df.head(self.limit), 
                       select_columns=self.columns,
                       justify={'index': rjust},
                       humanize={
                           'index': lambda i: str(i)+'.',
                           'published_parsed': lambda t: strftime("%b %d", t)
                        },
                       colorize={
                           'published_parsed': lambda t: f"[yellow]{t}[/yellow]",
                           'source': lambda t: f"[green]{t}[/green]"
                       },
                       print_header=False)

    
widget = FeedReader
from time import strftime

import feedparser
from pandas import DataFrame

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
        
        return df.head(self.limit)

    
widget = FeedReader
from urllib.parse import quote

import requests
from requests.exceptions import ConnectionError

from basemod import BaseModule


class Weather(BaseModule):
    __cache = ''
    
    def __init__(self, location:str, language:str=None,
                 narrow=False, metric:bool|None=None, speed_in_m_s=False,
                 today_forecast=False, tomorrow_forecast=False,
                 quiet=True, show_city=False, no_colors=False, console_glyphs=False,
                 **kwargs):
        self.location = quote(location)
        self.language = language
        self.narrow = narrow
        self.metric = metric
        self.speed_in_m_s = speed_in_m_s
        self.today_forecast = today_forecast
        self.tomorrow_forecast = tomorrow_forecast
        self.quiet = quiet
        self.show_city = show_city
        self.no_colors = no_colors
        self.console_glyphs = console_glyphs
        
        self.url = 'http://wttr.in/' + self.location + '?AF'
        if today_forecast and tomorrow_forecast:
            self.url += '2'         # current weather + today's + tomorrow's forecastc
        elif today_forecast:
            self.url += '1'         # current weather + today's forecast
        else:
            self.url += '0'         # only current weather
        
        if today_forecast and narrow:
            self.url += 'n'         # narrow version (only day and night)
        
        if quiet and not show_city:
            self.url += 'Q'         # superquiet version (no "Weather report", no city name)
        elif quiet:
            self.url += 'q'         # quiet version (no "Weather report" text)
        
        if no_colors:
            self.url += 'T'         # switch terminal sequences off (no colors)
            
        if console_glyphs:
            self.url += 'd'         # restrict output to standard console font glyphs
        
        if metric is True:
            self.url += 'm'         # metric (SI) (used by default everywhere except US)
        elif metric is False:
            self.url += 'u'         # USCS (used by default in US)
            
        if speed_in_m_s:
            self.url += 'M'         # show wind speed in m/s
        
        self.headers = {'User-Agent':'curl'}
        if language:
            self.headers['Accept-Language'] = language
        
        super().__init__(**kwargs)
        
        
    def __call__(self):
        try:
            self.__cache = requests.get(self.url, headers=self.headers).text
        except ConnectionError:
            pass
        
        return self.__cache
    
widget = Weather
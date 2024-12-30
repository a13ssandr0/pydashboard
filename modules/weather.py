from datetime import datetime

from basemod import BaseModule

import requests

class Weather(BaseModule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def __call__(self):
        t=requests.get('https://wttr.in/Reggio+Calabria?0AQd&lang=it', headers={'User-Agent':'curl'}).text
        # t = '\n'.join(t.splitlines()[2:7])
        return t
    
widget = Weather
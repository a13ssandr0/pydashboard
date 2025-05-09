from json import JSONDecodeError

from colorama import Fore, Style
from loguru import logger
from requests import get
from requests.exceptions import ConnectionError

from containers import BaseModule
from helpers.units import duration_fmt


def tick_to_seconds(ticks): return ticks / 10_000_000

class Jellyfin(BaseModule):
    def __init__(self, *, host, token, port=None, scheme='https', **kwargs):
        super().__init__(**kwargs)
        self.host=host
        self.token=token
        self.port=port
        self.scheme=scheme
        self.url = f'{scheme}://{host}'
        
        if self.port:
            self.url += f':{port}'
            
        self.url += '/Sessions?activeWithinSeconds=120'
        
        self.headers = {"Authorization": f"MediaBrowser Token={token}"}
        
    def __call__(self):
        try:
            sessions = get(self.url, headers=self.headers).json()
            users = ''
            for s in sessions:
                user = Style.BRIGHT + Fore.YELLOW + s['UserName'] + Style.RESET_ALL
                users += f"{user} @ {s['DeviceName']}\n"
                if s.get('NowPlayingItem'):
                    users += " "
                    if 'TranscodingInfo' in s:
                        users += Fore.RED + "T " + Style.RESET_ALL
                    curTime = duration_fmt(tick_to_seconds(s['PlayState']['PositionTicks'])).removeprefix('0:').split('.')[0]
                    totTime = duration_fmt(tick_to_seconds(s['NowPlayingItem']['RunTimeTicks'])).removeprefix('0:').split('.')[0]
                    users += f"{curTime}/{totTime}"
                    
                    season = s['NowPlayingItem'].get('ParentIndexNumber')
                    episode = s['NowPlayingItem'].get('IndexNumber')
                    if season is not None and episode is not None:
                        users += f" S{season}:E{episode}"
                    elif season is not None:
                        users += f" S{season}"
                    elif episode is not None:
                        users += f" E{episode}"
                    
                    title = s['NowPlayingItem']['Name']
                    users += f" - {title}\n"
            
            self.reset_settings('border_subtitle')
            self.reset_settings('styles.border_subtitle_color')

            return users
            
        except ConnectionError as e:
            self.border_subtitle = f'ConnectionError'
            self.styles.border_subtitle_color = 'red'
            logger.exception(str(e))
        except JSONDecodeError as e:
            self.border_subtitle = f'JSONDecodeError'
            self.styles.border_subtitle_color = 'red'
            logger.exception(str(e))
            
    
widget = Jellyfin
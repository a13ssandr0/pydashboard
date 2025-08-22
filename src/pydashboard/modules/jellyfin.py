from json import JSONDecodeError
from typing import Any

from requests import get
from requests.exceptions import ConnectionError

from pydashboard.containers import BaseModule
from pydashboard.utils.units import duration_fmt


def tick_to_seconds(ticks): return ticks / 10_000_000


class Jellyfin(BaseModule):
    def __init__(self, *, host: str, token: str, port: int = 443, scheme: str = 'https', **kwargs: Any):
        """

        Args:
            host: Jellyfin server IP or FQDN
            token: Jellyfin API token
            port: Jellyfin server port
            scheme: http or https
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(host=host, token=token, port=port, scheme=scheme, **kwargs)
        self.host = host
        self.token = token
        self.port = port
        self.scheme = scheme
        self.url = f'{scheme}://{host}:{port}/Sessions?activeWithinSeconds=120'
        self.headers = {"Authorization": f"MediaBrowser Token={token}"}

    def __call__(self):
        try:
            response = get(self.url, headers=self.headers)

            try:
                sessions = response.json()
            except JSONDecodeError as e:
                self.border_subtitle = f'JSONDecodeError'
                self.styles.border_subtitle_color = 'red'
                self.logger.critical(str(e))
                self.logger.debug(response.text)
                return None

            users = ''
            for s in sessions:
                users += f"[yellow]{s.get('UserName', '')}[/yellow] @ {s.get('DeviceName', '')}\n"
                if s.get('NowPlayingItem'):
                    users += " "
                    if 'TranscodingInfo' in s:
                        users += "[red]T[/red] "
                    cur_time = \
                        duration_fmt(tick_to_seconds(s.get('PlayState', {}).get('PositionTicks', 0))).removeprefix(
                                '0:').split('.')[0]
                    tot_time = \
                        duration_fmt(tick_to_seconds(s['NowPlayingItem'].get('RunTimeTicks', 0))).removeprefix(
                                '0:').split('.')[0]
                    users += f"{cur_time}/{tot_time}"

                    if 'SeriesName' in s['NowPlayingItem']:
                        users += " " + s['NowPlayingItem']['SeriesName']

                        season = s['NowPlayingItem'].get('ParentIndexNumber')
                        episode = s['NowPlayingItem'].get('IndexNumber')
                        if season is not None and episode is not None:
                            users += f" S{season}:E{episode}"
                        elif season is not None:
                            users += f" S{season}"
                        elif episode is not None:
                            users += f" E{episode}"

                    users += f" - {s['NowPlayingItem'].get('Name', '')}\n"  # title

            self.reset_settings('border_subtitle')
            self.reset_settings('styles.border_subtitle_color')

            return users

        except ConnectionError as e:
            self.border_subtitle = f'ConnectionError'
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))



widget = Jellyfin

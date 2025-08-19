from typing import Any
from urllib.parse import quote

import requests
from requests.exceptions import ConnectionError
from rich.text import Text

from pydashboard.containers import BaseModule


class Weather(BaseModule):
    __cache = ''

    def __init__(self, location: str, language: str = None, narrow: bool = False, metric: bool = None,
                 speed_in_m_s: bool = False, today_forecast: bool = False, tomorrow_forecast: bool = False,
                 quiet: bool = True, show_city: bool = False, no_colors: bool = False, console_glyphs: bool = False,
                 **kwargs: Any):
        """
        See [wttr.in/:help](https://wttr.in/:help)

        Args:
            location: See [Supported location types](#supported-location-types)
            language: Show weather information in this language
            narrow: Show only day and night
            metric: Show units using the metric system (SI) (used by default everywhere except US)
            speed_in_m_s: Show wind speed in m/s
            today_forecast: Show current weather and today forecast
            tomorrow_forecast: Show current weather, today forecast and tomorrow forecast. If True, `today_forecast` will be ignored.
            quiet: Be quiet: no "Weather report" text
            show_city: Super quiet: hide city name. Requires "quiet=True"
            no_colors: Disable colored output
            console_glyphs: If true disables use of advanced terminal features like emojis.
            **kwargs: See [BaseModule](../containers/basemodule.md)


        # Supported location types

        | Example               |Description                                  |
        |-----------------------|---------------------------------------------|
        |`paris`                | city name                                   |
        |`~Eiffel+tower`        | any location (+ for spaces)                 |
        |`Москва`               | Unicode name of any location in any language|
        |`muc`                  | airport code (3 letters)                    |
        |`@stackoverflow.com`   | domain name                                 |
        |`94107`                | area codes                                  |
        |`-78.46,106.79`        | GPS coordinates                             |

        Location also supports moon phase information:

        | Example               |Description                                          |
        |-----------------------|-----------------------------------------------------|
        |`moon`                 | Moon phase (add ,+US or ,+France for these cities)  |
        |`moon@2016-10-25`      | Moon phase for the date (@2016-10-25)               |

        !!! warning
            Refer to [wttr.in](https://wttr.in/:help) documentation for updated supported location types.

        """
        super().__init__(location=location, language=language, narrow=narrow, metric=metric, speed_in_m_s=speed_in_m_s,
                         today_forecast=today_forecast, tomorrow_forecast=tomorrow_forecast, quiet=quiet,
                         show_city=show_city, no_colors=no_colors, console_glyphs=console_glyphs, **kwargs)
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

        # noinspection HttpUrlsUsage
        self.url = 'http://wttr.in/' + self.location + '?AF'
        if tomorrow_forecast:
            self.url += '2'  # current weather + today's + tomorrow's forecastc
        elif today_forecast:
            self.url += '1'  # current weather + today's forecast
        else:
            self.url += '0'  # only current weather

        if today_forecast and narrow:
            self.url += 'n'  # narrow version (only day and night)

        if quiet and not show_city:
            self.url += 'Q'  # superquiet version (no "Weather report", no city name)
        elif quiet:
            self.url += 'q'  # quiet version (no "Weather report" text)

        if no_colors:
            self.url += 'T'  # switch terminal sequences off (no colors)

        if console_glyphs:
            self.url += 'd'  # restrict output to standard console font glyphs

        if metric:
            self.url += 'm'  # metric (SI) (used by default everywhere except US)
        elif metric is False:
            self.url += 'u'  # USCS (used by default in US)

        if speed_in_m_s:
            self.url += 'M'  # show wind speed in m/s

        self.headers = {'User-Agent': 'curl/8.12.1'}
        if language:
            self.headers['Accept-Language'] = language

    def __call__(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            if response.status_code == 200:
                self.__cache = Text.from_ansi(response.text)
                self.reset_settings('border_subtitle')
                self.reset_settings('styles.border_subtitle_color')
            else:
                self.border_subtitle = f'{response.status_code} {response.reason}'
                self.styles.border_subtitle_color = 'red'
                self.logger.error(response.text)
        except ConnectionError as e:
            self.logger.critical(str(e))

        return self.__cache


widget = Weather

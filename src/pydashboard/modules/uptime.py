from datetime import timedelta
from typing import Any, Literal

from pydashboard.containers import BaseModule


class Uptime(BaseModule):

    def __init__(self, *, compact: bool | Literal[0, 1, 2] = False, show_prefix: bool = True,
                 show_seconds: bool = False, **kwargs: Any):
        """

        Args:
            compact:
                | Value     | Result                                |
                |----------:|---------------------------------------|
                |0 or False | 5 days, 4 hours, 3 minutes, 2 seconds |
                |1 or True  | 5 d, 4 h, 3 m, 2 s                    |
                |2          | 5d 04:03:02                           |
            show_prefix: Show "uptime" or "up" prefix
            show_seconds: Also show seconds
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(compact=compact, show_prefix=show_prefix, show_seconds=show_seconds, **kwargs)
        self.compact = compact
        self.show_prefix = show_prefix
        self.show_seconds = show_seconds

    def __call__(self):
        with open('/proc/uptime') as f:
            td = timedelta(seconds=float(f.readline().split()[0]))

        uptime = ''

        if self.show_prefix:
            uptime += 'up ' if self.compact else 'uptime '

        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if self.compact != 2:
            d = f'{days} d'
            h = f'{hours} h'
            m = f'{minutes} m'
            s = f'{seconds % 60} s'

            if not self.compact:
                d += 'ay' + ('s' if days != 1 else '')
                h += 'our' + ('s' if hours != 1 else '')
                m += 'inute' + ('s' if minutes != 1 else '')
                s += 'econd' + ('s' if seconds % 60 != 1 else '')

            return uptime + ', '.join((d, h, m, s) if self.show_seconds else (d, h, m))
        else:
            return uptime + f'{days}d {hours:02}:{minutes:02}' + (f':{seconds:02}' if self.show_seconds else '')


widget = Uptime

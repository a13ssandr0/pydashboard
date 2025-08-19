import socket
from collections import OrderedDict
from datetime import datetime, timedelta
from math import isnan
from typing import Any, Literal

from pydashboard.containers import BaseModule
from pydashboard.utils.bars import calc_bars_sizes, create_bar
from pydashboard.utils.types import Size

CMD_STATUS = b"\x00\x06status"
EOF = b"  \n\x00\x00"
SEP = ":"
BUFFER_SIZE = 1024
ALL_UNITS = (
    "Minutes",
    "Seconds",
    "Percent",
    "Volts",
    "Watts",
    "Amps",
    "Hz",
    "C",
    "VA",
    "Percent Load Capacity"
)


class APCUPSd(BaseModule):

    def __init__(self, *, title: str = None, host: str = "localhost", port: int = 3551, timeout: int = 30,
                 bars: Literal['auto', 0, 1, 2] = 0, **kwargs: Any):
        """
        Args:
            title: if not set or null defaults to ups model
            host: APCUPSd server address
            port: APCUPSd server port
            timeout: Connection timeout seconds
            bars: Whether to show status bars on 1 or 2 lines or automatically ('auto', 0)
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(title=title, host=host, port=port, timeout=timeout, bars=bars, **kwargs)
        self.host = host
        self.port = port
        self.timeout = timeout
        self.bars = bars
        self.__model_as_title = title is None

    def __post_init__(self, content_size: Size):
        self.bars, self.lbar, self.rbar = calc_bars_sizes(content_size[1], self.bars)

    def __call__(self, content_size: Size):
        try:
            data = self.get()
        except TimeoutError:
            return '[red]Connection timed out[/red]'
        except ConnectionRefusedError:
            return '[red]Offline or connection refused[/red]'

        if self.__model_as_title and 'MODEL' in data:
            self.border_title = data['MODEL']

        return self.render_ups(data, content_size[1])

    def render_ups(self, data, content_width):
        ups_status = data.get('STATUS', 'N/A')
        input_voltage = float(data.get('LINEV', 'nan'))
        battery_charge = float(data.get('BCHARGE', 'nan'))
        battery_low = 20
        battery_warning = 30
        ups_load = round(float(data.get('LOADPCT', -1)))
        ups_load_warn = 60
        ups_load_high = 90
        if 'LOADPCT' in data and 'NOMPOWER' in data:
            load_power = round(ups_load * float(data['NOMPOWER']) / 100)
        else:
            load_power = None
        battery_runtime = round(float(data.get('TIMELEFT', 'nan')), 1)
        if 'LASTXFER' in data:
            last_xfer_reason = data['LASTXFER'][0].upper() + data['LASTXFER'][1:]
        else:
            last_xfer_reason = None

        if ups_status == 'N/A':
            name_color = 'red'
        else:
            name_color = 'yellow' if 'OFF' not in ups_status else 'green'
        load_color = 'green' if ups_load < ups_load_warn else ('yellow' if ups_load < ups_load_high else 'red')
        batt_color = 'green' if battery_charge > battery_warning else (
            'yellow' if battery_charge > battery_low else 'red')

        load_power = f'{load_power}W ' if load_power is not None else ''
        if ups_load > -1:
            load_bar = create_bar(self.lbar, ups_load, f'{load_power}{ups_load}%', '', load_color)
        else:
            load_bar = load_power

        battery_runtime = f'{battery_runtime}m ' if not isnan(battery_runtime) else ''
        if not isnan(battery_charge):
            batt_bar = create_bar(self.rbar, battery_charge,
                                  f'{battery_runtime}{battery_charge}%', '', batt_color)
        else:
            batt_bar = battery_runtime

        input_voltage = f' {round(input_voltage)}V' if not isnan(input_voltage) else ''
        spaces = content_width - len(ups_status + input_voltage)
        if spaces < 2:
            ups_status = ups_status[:spaces - 2]
            spaces = 2

        header = f"[{name_color}]{ups_status}[/{name_color}]" + ' ' * spaces + input_voltage + '\n'
        if 'REPLACEBATT' in ups_status:
            # highlight in event of replace battery warning
            header = f'[on red]{header}[/on red]'

        return (
                header
                + load_bar + ('\n' if self.bars == 2 else '') + batt_bar + '\n'
                + f'  Last: {last_xfer_reason}'
        )

    def get(self):
        """
        Connect to the APCUPSd NIS and request its status.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            sock.send(CMD_STATUS)
            buffr = b""
            while not buffr.endswith(EOF):
                buffr += sock.recv(BUFFER_SIZE)
        return self.parse(buffr.decode(), True)

    def parse(self, raw_status, strip_units=False):
        """
        Split the output from get_status() into lines, clean it up and return it as
        an OrderedDict.
        """
        # Remove the EOF string, split status on the line endings (\x00), strip the
        # length byte and newline chars off the beginning and end respectively.
        lines = [x[1:-1] for x in raw_status[:-len(EOF)].split("\x00") if x]
        if strip_units:
            lines = self.strip_units_from_lines(lines)
        # Split each line on the SEP character, strip extraneous whitespace and
        # create an OrderedDict out of the keys/values.
        return OrderedDict([[x.strip() for x in x.split(SEP, 1)] for x in lines])

    @staticmethod
    def strip_units_from_lines(lines):
        """
        Removes all units from the ends of the lines.
        """
        for line in lines:
            for unit in ALL_UNITS:
                if line.endswith(" %s" % unit):
                    line = line[:-1 - len(unit)]
            yield line

    @staticmethod
    def human_readable_time(timestr):
        try:
            delta: timedelta = datetime.now() - datetime.strptime(timestr.split(' +')[0], "%Y-%m-%d %H:%M:%S")
            if delta.days:
                return f"{delta.days}d ago"
            elif delta.seconds:
                minutes, seconds = divmod(delta.seconds, 60)
                hours, minutes = divmod(minutes, 60)
                if hours:
                    return f"{hours}h ago"
                elif minutes:
                    return f"{minutes}m ago"
                else:
                    return f"{seconds}s ago"
        except:
            return timestr


widget = APCUPSd

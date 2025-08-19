from math import isnan
from os import environ
from typing import Any, Literal

from pydashboard.containers import BaseModule
from pydashboard.utils.bars import calc_bars_sizes, create_bar
from pydashboard.utils.types import Size

environ['PWNLIB_NOTERM'] = 'true'
from pwnlib.exception import PwnlibException
from pwnlib.tubes.remote import remote


class NUT(BaseModule):
    def __init__(self, *, title: str = None, host: str = "localhost", port: int = 3493, upsname: str = None,
                 username: str = None, password: str = None, timeout: int = 30, bars: Literal['auto', 0, 1, 2] = 0,
                 **kwargs: Any):
        """
        Displays information about UPSes connected to a Network Ups Tools server.

        Args:
            title: if not set or null defaults to ups name if upsname is set
            host: NUT server IP or FQDN
            port: NUT server port
            upsname: UPS name, if not set or null all UPSes will be shown
            username: NUT username
            password: NUT password
            timeout: Connection timeout seconds
            bars: whether to show status bars on 1 or 2 lines or automatically ('auto', 0)
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(title=title, host=host, port=port, upsname=upsname, username=username, password=password,
                         timeout=timeout, bars=bars, **kwargs)
        self.username = username
        self.password = password
        self.upsname = upsname
        self.host = host
        self.port = port
        self.timeout = timeout
        self.bars = bars
        self.__model_as_title = title is None and upsname is not None

    def __post_init__(self, content_size: Size):
        self.bars, self.lbar, self.rbar = calc_bars_sizes(content_size[1], self.bars)

    def __call__(self, content_size: Size):
        try:
            status = self.get()
        except TimeoutError:
            return '[red]Connection timed out[/red]'
        except ConnectionRefusedError:
            return '[red]Offline or connection refused[/red]'
        except RuntimeError as e:
            return f"[red]{e}[/red]"
        except PwnlibException as e:
            return f"[red]{e}[/red]"

        if self.__model_as_title:
            self.border_title = status[self.upsname]['friendly_name']

        return '\n'.join(self.render_ups(data, content_size[1]) for _, data in status.items())

    def render_ups(self, data, content_width):
        friendly_name = data['friendly_name']
        if 'error' in data:
            return f"[red]{friendly_name}\n{data['error']}[/red]"

        ups_status = data.get('ups-status', 'N/A')
        input_voltage = float(data.get('input-voltage', 'nan'))
        battery_charge = float(data.get('battery-charge', 'nan'))
        battery_low = int(data.get('battery-charge-low', '20'))
        battery_warning = int(data.get('battery-charge-warning', str(battery_low + 10)))
        ups_load = int(data.get('ups-load', -1))
        ups_load_warn = int(data.get('ups-load-warning', '60'))
        ups_load_high = int(data.get('ups-load-high', '90'))
        if 'ups-realpower' in data:
            load_power = int(data['ups-realpower'])
        elif 'ups-realpower-nominal' in data:
            load_power = round(ups_load * float(data['ups-realpower-nominal']) / 100)
        else:
            load_power = None
        battery_runtime = round(float(data.get('battery-runtime', 'nan')) / 60, 1)
        if 'input-transfer-reason' in data:
            last_xfer_reason = data['input-transfer-reason'][0].upper() + data['input-transfer-reason'][1:]
        else:
            last_xfer_reason = None

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

        if not isnan(input_voltage):
            ups_status += f' {round(input_voltage)}V'
        spaces = content_width - len(friendly_name + ups_status)
        if spaces < 2:
            friendly_name = friendly_name[:spaces - 2]
            spaces = 2

        header = f"[{name_color}]{friendly_name}[/{name_color}]" + ' ' * spaces + ups_status + '\n'
        if 'RB' in ups_status:
            # highlight in event of replace battery warning
            header = f'[on red]{header}[/on red]'

        return (
                header
                + load_bar + ('\n' if self.bars == 2 else '') + batt_bar + '\n'
                + f'  Last: {last_xfer_reason}'
        )

    def get(self):
        with remote(self.host, self.port, timeout=self.timeout) as sock:
            self.login(sock)

            try:
                ups_list = self.get_ups_names(sock)
            except RuntimeError as e:
                if self.upsname:
                    # cannot get friendly name, at least try to get UPS data
                    ups_list = {self.upsname: self.upsname}
                else:
                    raise e

            if self.upsname:
                result = {
                    self.upsname: self.get_ups_vars(sock, self.upsname) | {'friendly_name': ups_list[self.upsname]}
                }
            else:
                result = {
                    k: self.get_ups_vars(sock, k) | {'friendly_name': v}
                    for k, v in ups_list.items()
                }

            sock.sendline(b'LOGOUT')
            return result

    def login(self, sock):
        if self.username is not None:
            sock.sendline(f"USERNAME {self.username}".encode())
            result = sock.recvline(False).decode()
            if result[:2] != "OK":
                raise RuntimeError(result)
        if self.password is not None:
            sock.sendline(f"PASSWORD \"{self.password}\"".encode())
            result = sock.recvline(False).decode()
            if result[:2] != "OK":
                raise RuntimeError(result)

    @staticmethod
    def get_ups_vars(sock, upsname):
        sock.sendline(f"LIST VAR {upsname}".encode())
        result = sock.recvline(False).decode()
        if "BEGIN LIST VAR" not in result:
            return {'error': result}
        result = sock.recvuntil(f"END LIST VAR {upsname}\n".encode()).decode()
        return {l[0].replace('.', '-'): l[1].strip('"') for l in
                [l.split(maxsplit=1) for l in result.replace(f'VAR {upsname} ', '').splitlines()[:-1]]}

    @staticmethod
    def get_ups_names(sock):
        sock.sendline(b"LIST UPS")
        result = sock.recvline(False).decode()
        if "BEGIN LIST UPS" not in result:
            raise RuntimeError(result)
        result = sock.recvuntil(b"END LIST UPS\n").decode().splitlines()[:-1]
        return {l[1]: l[2].strip('"') for l in [l.split(maxsplit=2) for l in result]}


widget = NUT

from math import ceil, floor
from os import environ

from helpers.bars import create_bar

environ['PWNLIB_NOTERM'] = 'true'

from pwnlib.tubes.remote import remote
from containers import BaseModule


class NUT(BaseModule):
    def __init__(self, *, title=None, host="localhost", port=3493, upsname: str = None, username: str = None,
                 password: str = None, timeout=30, **kwargs):
        super().__init__(title=title, **kwargs)
        self.username = username
        self.password = password
        self.upsname = upsname
        self.host = host
        self.port = port
        self.timeout = timeout
        self.__model_as_title = title is None and upsname is not None

    def __call__(self):
        try:
            status = self.get()
        except TimeoutError:
            return 'Connection timed out'
        except ConnectionRefusedError:
            return 'Offline or connection refused'

        if self.__model_as_title:
            self.border_title = status[self.upsname]['friendly_name']

        result = ''
        for _, data in status.items():
            result += self.render_ups(data)

        return result

    def render_ups(self, data):
        ups_status = data['ups-status']
        input_voltage = round(float(data['input-voltage']))
        battery_charge = int(data['battery-charge'])
        battery_low = int(data['battery-charge-low'])
        battery_warning = int(data['battery-charge-warning']) if 'battery-charge-warning' in data else battery_low + 10
        ups_load = int(data['ups-load'])
        ups_load_warn = int(data['ups-load-warning']) if 'ups-load-warning' in data else 60
        ups_load_high = int(data['ups-load-high']) if 'ups-load-high' in data else 90
        if 'ups-realpower' in data:
            load_power = int(data['ups-realpower'])
        else:
            load_power = round(float(data['ups-load']) * float(data['ups-realpower-nominal']) / 100)
        battery_runtime = round(int(data['battery-runtime']) / 60, 1)
        last_xfer_reason = (data['input-transfer-reason'][0].upper() + data['input-transfer-reason'][1:]) \
            if 'input-transfer-reason' in data else 'None'

        result = ''

        ups_status += f' {input_voltage}V'
        spaces = self.content_size.width - len(data['friendly_name'] + ups_status)
        name_color = 'yellow' if 'OFF' not in ups_status else 'green'
        load_color = 'green' if ups_load<ups_load_warn else ('yellow' if ups_load<ups_load_high else 'red')
        batt_color = 'green' if battery_charge>battery_warning else ('yellow' if battery_charge>battery_low else 'red')
        result += (
                f"[{name_color}]{data['friendly_name']}[/{name_color}]" + ' ' * spaces + ups_status + '\n'
                +
                create_bar(ceil(self.content_size.width / 2), ups_load, f'{load_power}W {ups_load}%', '', load_color)
                +
                create_bar(floor(self.content_size.width / 2), battery_charge, f'{battery_runtime}m {battery_charge}%',
                           '', batt_color)
                + '\n  Last: ' + last_xfer_reason + '\n'
        )

        return result

    def get(self):
        with remote(self.host, self.port, timeout=self.timeout) as sock:
            self.login(sock)

            ups_list = self.get_ups_names(sock)

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

    def get_ups_vars(self, sock, upsname):
        sock.sendline(f"LIST VAR {upsname}".encode())
        result = sock.recvline(False).decode()
        if "BEGIN LIST VAR" not in result:
            raise RuntimeError(result)
        result = sock.recvuntil(f"END LIST VAR {upsname}\n".encode()).decode()
        return {l[0].replace('.', '-'): ' '.join(l[1:]).strip('"') for l in
                [l.split() for l in result.replace(f'VAR {upsname} ', '').splitlines()[:-1]]}

    def get_ups_names(self, sock):
        sock.sendline(b"LIST UPS")
        result = sock.recvline(False).decode()
        if "BEGIN LIST UPS" not in result:
            raise RuntimeError(result)
        result = sock.recvuntil(b"END LIST UPS\n").decode().splitlines()[:-1]
        return {l[1]: ' '.join(l[2:]).strip('"') for l in [l.split() for l in result]}


widget = NUT

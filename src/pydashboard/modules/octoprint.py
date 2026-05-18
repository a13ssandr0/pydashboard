import json
from json import JSONDecodeError
from typing import Any

import requests
from benedict import benedict
from octorest import OctoRest

from pydashboard.containers import BaseModule
from pydashboard.utils.units import duration_fmt


class OctoPrint(BaseModule):
    def __init__(self, *, host: str, token: str, port: int = 80, scheme: str = 'http', **kwargs: Any):
        """

        Args:
            host: OctoPrint server IP or FQDN
            token: OctoPrint API token
            port: OctoPrint server port
            scheme: http or https
            **kwargs: See [BaseModule](../containers/basemodule.md)

        !!! note
            This widget ignores `subtitle`, `subtitle_align`, `subtitle_background`, `subtitle_color` and
            `subtitle_style` because they are used internally to display status.
        """
        for k in ['subtitle', 'subtitle_align', 'subtitle_background', 'subtitle_color', 'subtitle_style']:
            if k in kwargs:
                del kwargs[k]
        super().__init__(host=host, token=token, port=port, scheme=scheme, **kwargs)
        self.host = host
        self.token = token
        self.port = port
        self.scheme = scheme
        self.url = f'{scheme}://{host}:{port}'
        self.styles.border_subtitle_align = 'left'

        def _check_response(_, response: 'requests.Response'):
            """
            Make sure the response status code was 20x, raise otherwise
            """
            if not (200 <= response.status_code < 210):
                error = response.text
                msg = (f'Reply for {response.url} was not OK: {response.status_code} {response.reason}\n'
                       '-----\n'
                       f'{error}')
                raise RuntimeError(msg)
            return response

        # patch `_check_response` method to change exception formatting
        OctoRest._check_response = _check_response

    def __call__(self):
        out = ''
        try:
            client = OctoRest(url=self.url, apikey=self.token)
            job_info = benedict(client.job_info(), keyattr_dynamic=True)
            conn_info = benedict(client.connection_info(), keyattr_dynamic=True)
            printer = benedict(client.printer() if conn_info.current.port else {}, keyattr_dynamic=True)

            out = f"State: {job_info.state}\n"
            if (filename := job_info.job.file.name) is not None:
                out += f"File: {filename}\n"
            if (completion := job_info.progress.completion) is not None:
                out += f'Progress: {completion:.3f}%' + '\n'
            if (printTime := job_info.progress.printTime) is not None:
                out += f'Print time: {duration_fmt(printTime)}s' + '\n'
            if (printTimeLeft := job_info.progress.printTimeLeft) is not None:
                out += f'Time left: {duration_fmt(printTimeLeft)}s' + '\n'

            conn_state = conn_info.current.state
            self.border_subtitle = conn_state
            self.styles.border_subtitle_color = 'green' if conn_state != 'Closed' and 'error' not in conn_state.lower() else 'red'

            if conn_info.current.port is not None and (temperatures := printer.temperature):
                max_len = max([len(x) for x in temperatures.keys()])
                out += 'Temperatures:' + '\n'
                for tool, temp in temperatures.items():
                    if not temp.actual and not temp.offset and not temp.target:
                        # Exclude empty sensors
                        continue
                    out += ' ' + tool.ljust(max_len) + ' '
                    if (actual := temp.actual) is not None:
                        out += f"{actual:.1f}°C"
                    else:
                        out += 'N/A'
                    if (target := temp.target) is not None:
                        if target:
                            out += f"/{target:.1f}°C\n"
                        else:
                            out += '/off\n'
                    else:
                        out += '/N/A\n'

        except RuntimeError as e:
            try:
                error = e.args[0].split('-----', maxsplit=1)[1]
                error = json.loads(error)
                error = error['error']
            except (IndexError, JSONDecodeError, KeyError):
                error = e.args[0].splitlines()[0].split(':')[1].strip()

            self.border_subtitle = error
            self.styles.border_subtitle_color = 'red'

        except OSError:
            self.border_subtitle = 'Offline'
            self.styles.border_subtitle_color = 'red'

        return out


widget = OctoPrint

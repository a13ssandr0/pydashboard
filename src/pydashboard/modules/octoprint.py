from typing import Any

from octorest import OctoRest
from requests.packages import target

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

    def __call__(self):
        try:
            out = ''
            client = OctoRest(url=self.url, apikey=self.token)
            job_info = client.job_info()
            out += f"State: {job_info['state']}\n"
            out += f"File: {job_info['job']['file']['name']}\n"
            if (completion:=job_info.get('progress', {}).get('completion')) is not None:
                out += f'Progress: {completion:.3f}%' + '\n'
            if (printTime:=job_info.get('progress', {}).get('printTime')) is not None:
                out += f'Print time: {duration_fmt(printTime)}s' + '\n'
            if (printTimeLeft:=job_info.get('progress', {}).get('printTimeLeft')) is not None:
                out += f'Time left: {duration_fmt(printTimeLeft)}s' + '\n'

            conn_info = client.connection_info()
            b_sub = conn_info.get('current', {}).get('state', 'N/A')
            self.border_subtitle = b_sub
            self.styles.border_subtitle_color = 'green' if b_sub != 'N/A' else 'red'
            if conn_info.get('current', {}).get('port') is not None:
                printer = client.printer()
                temperatures = printer.get('temperature', {})
                if temperatures:
                    max_len = max([len(x) for x in temperatures.keys()])
                    out += 'Temperatures:' + '\n'
                    for tool, temp in temperatures.items():
                        if not temp.get('actual') and not temp.get('offset') and not temp.get('target'):
                            #Exclude empty sensors
                            continue
                        out += ' ' + tool.ljust(max_len) + ' '
                        if (actual:=temp.get('actual')) is not None:
                            out += f"{actual:.1f}°C"
                        else:
                            out += 'N/A'
                        if (target:=temp.get('target')) is not None:
                            if target:
                                out += f"/{target:.1f}°C\n"
                            else:
                                out += '/off\n'
                        else:
                            out += '/N/A\n'

            return out

        except OSError:
            self.border_subtitle = 'Offline'
            self.styles.border_subtitle_color = 'red'


widget = OctoPrint

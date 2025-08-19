from typing import Any

from octorest import OctoRest

from pydashboard.containers import BaseModule


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
            out += 'State:', job_info['state'] + '\n'
            out += 'File:', job_info['job']['file']['name'] + '\n'
            if job_info['progress']['completion'] is not None:
                out += 'Progress: {:.3f}%'.format(job_info['progress']['completion']) + '\n'
            if job_info['progress']['printTime'] is not None:
                out += 'Print time: {}s'.format(job_info['progress']['printTime']) + '\n'
            if job_info['progress']['printTimeLeft'] is not None:
                out += 'Time left: {}s'.format(job_info['progress']['printTimeLeft']) + '\n'

            conn_info = client.connection_info()
            self.border_subtitle = conn_info['current']['state']
            self.styles.border_subtitle_color = 'green'
            if conn_info['current']['port'] is not None:
                printer = client.printer()
                max_len = max([len(x) for x in printer['temperature'].keys()])
                out += 'Temperatures:' + '\n'
                for tool, temp in printer['temperature'].items():
                    if temp['target']:
                        out += ' ', tool.ljust(max_len), f"{temp['actual']:.1f}°C/{temp['target']:.1f}°C" + '\n'
                    else:
                        out += ' ', tool.ljust(max_len), f"{temp['actual']:.1f}°C/off" + '\n'

            return out

        except OSError:
            self.border_subtitle = 'Offline'
            self.styles.border_subtitle_color = 'red'


widget = OctoPrint

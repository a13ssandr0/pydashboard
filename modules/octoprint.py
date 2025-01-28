from octorest import OctoRest

from containers import BaseModule


class Octoprint(BaseModule):
    def __init__(self, *, host, token, port=80, scheme='http', subtitle=None, subtitle_align=None, subtitle_background=None, subtitle_color=None, subtitle_style=None, **kwargs):
        self.host=host
        self.token=token
        self.port=port
        self.scheme=scheme
        self.url = f'{scheme}://{host}:{port}'
        super().__init__(**kwargs)
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
                        out += ' ', tool.ljust(max_len), f'{temp['actual']:.1f}°C/{temp['target']:.1f}°C' + '\n'
                    else:
                        out += ' ', tool.ljust(max_len), f'{temp['actual']:.1f}°C/off' + '\n'

            return out

        except OSError:
            self.border_subtitle = 'Offline'
            self.styles.border_subtitle_color = 'red'
    
widget = Octoprint






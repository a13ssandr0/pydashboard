from pandas import DataFrame
from requests import JSONDecodeError, Session
from requests.exceptions import ConnectionError

from pydashboard.containers import TableModule
from pydashboard.utils import noneg
from pydashboard.utils.units import duration_fmt, perc_fmt, sizeof_fmt, speedof_fmt, time_fmt

states_map = {
    'allocating'        : 'A',
    'downloading'       : 'D',
    'checkingDL'        : 'CD',
    'forcedDL'          : 'FD',
    'metaDL'            : 'MD',
    'pausedDL'          : 'PD',
    'queuedDL'          : 'QD',
    'stalledDL'         : 'SD',
    'error'             : 'E',
    'missingFiles'      : 'MF',
    'uploading'         : 'U',
    'checkingUP'        : 'CU',
    'forcedUP'          : 'FU',
    'pausedUP'          : 'PU',
    'queuedUP'          : 'QU',
    'stalledUP'         : 'SU',
    'queuedChecking'    : 'QC',
    'checkingResumeData': 'CR',
    'moving'            : 'MV',
    'unknown'           : '?',
}

colors_map = {
    "A" : "green",
    "D" : "green",
    "CD": "yellow",
    "FD": "cyan",
    "MD": "blue",
    "PD": "bright_black",
    "QD": "blue",
    "SD": "yellow",
    "E" : "red",
    "MF": "red",
    "U" : "green",
    "CU": "yellow",
    "FU": "cyan",
    "PU": "bright_black",
    "QU": "blue",
    "SU": "yellow",
    "QC": "blue",
    "CR": "yellow",
    "MV": "green",
    "?" : "magenta"
}

_justify = {
    'added_on'          : 'left',
    'amount_left'       : 'right',
    'auto_tmm'          : 'left',
    'availability'      : 'right',
    'category'          : 'left',
    'completed'         : 'right',
    'completion_on'     : 'left',
    'content_path'      : 'left',
    'dl_limit'          : 'right',
    'dlspeed'           : 'right',
    'downloaded'        : 'right',
    'downloaded_session': 'right',
    'eta'               : 'left',
    'f_l_piece_prio'    : 'left',
    'force_start'       : 'left',
    'hash'              : 'left',
    'isPrivate'         : 'left',
    'last_activity'     : 'left',
    'magnet_uri'        : 'left',
    'max_ratio'         : 'right',
    'max_seeding_time'  : 'left',
    'name'              : 'left',
    'num_complete'      : 'right',
    'num_incomplete'    : 'right',
    'num_leechs'        : 'right',
    'num_seeds'         : 'right',
    'priority'          : 'right',
    'progress'          : 'right',
    'ratio'             : 'right',
    'ratio_limit'       : 'right',
    'save_path'         : 'left',
    'seeding_time'      : 'left',
    'seeding_time_limit': 'left',
    'seen_complete'     : 'left',
    'seq_dl'            : 'left',
    'size'              : 'right',
    'state'             : 'right',
    'super_seeding'     : 'left',
    'tags'              : 'left',
    'time_active'       : 'left',
    'total_size'        : 'right',
    'tracker'           : 'left',
    'up_limit'          : 'right',
    'uploaded'          : 'right',
    'uploaded_session'  : 'right',
    'upspeed'           : 'right',
}

_human = {
    'added_on'          : duration_fmt,
    'amount_left'       : sizeof_fmt,
    # 'auto_tmm':           noop,
    'availability'      : perc_fmt,
    # 'category':           noop,
    'completed'         : sizeof_fmt,
    'completion_on'     : time_fmt,
    # 'content_path':       noop,
    'dl_limit'          : speedof_fmt,
    'dlspeed'           : speedof_fmt,
    'downloaded'        : sizeof_fmt,
    'downloaded_session': sizeof_fmt,
    'eta'               : duration_fmt,
    # 'f_l_piece_prio':     noop,
    # 'force_start':        noop,
    # 'hash':               noop,
    # 'isPrivate':          noop,
    'last_activity'     : time_fmt,
    # 'magnet_uri':         noop,
    'max_ratio'         : perc_fmt,
    'max_seeding_time'  : duration_fmt,
    # 'name':               noop,
    # 'num_complete':       noop,
    # 'num_incomplete':     noop,
    # 'num_leechs':         noop,
    # 'num_seeds':          noop,
    'priority'          : noneg,
    'progress'          : perc_fmt,
    'ratio'             : perc_fmt,
    'ratio_limit'       : perc_fmt,
    # 'save_path':          noop,
    'seeding_time'      : duration_fmt,
    'seeding_time_limit': duration_fmt,
    'seen_complete'     : time_fmt,
    # 'seq_dl':             noop,
    'size'              : sizeof_fmt,
    'state'             : lambda s: states_map.get(s, '?'),
    # 'super_seeding':      noop,
    # 'tags':               noop,
    'time_active'       : duration_fmt,
    'total_size'        : sizeof_fmt,
    # 'tracker':            noop,
    'up_limit'          : speedof_fmt,
    'uploaded'          : sizeof_fmt,
    'uploaded_session'  : sizeof_fmt,
    'upspeed'           : speedof_fmt,
}


def colorize(state):
    c = colors_map.get(state, colors_map['?'])
    return f'[{c}]{state}[/{c}]'


class BitTorrent(TableModule):
    justify = _justify
    colorize = {'state': colorize}

    def __init__(self, *, host, username, password, port=8080, scheme='http',
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] = ('downloaded', False),
                 columns=None, human_readable=True, show_header=False, **kwargs):
        """

        Args:
            host:
            username:
            password:
            port:
            scheme:
            sort:
            columns:
            human_readable:
            show_header:
            **kwargs: See [TableModule](../containers/tablemodule.md)
        """
        if columns is None:
            columns = ['state', 'progress', 'ratio', 'name']
        super().__init__(host=host, username=username, password=password, port=port, scheme=scheme,
                         human_readable=human_readable, columns=columns, show_header=show_header, sort=sort, **kwargs)
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.scheme = scheme
        self.humanize = _human if human_readable else None
        self.referer = f'{scheme}://{host}:{port}'
        self.url = f'{scheme}://{host}:{port}/api/v2/auth/login'

    def __post_init__(self):
        self.session = Session()
        try:
            self.session.post(self.url,
                              data={"username": self.username, "password": self.password},
                              headers={'Referer': self.referer})
        except ConnectionError as e:
            self.border_subtitle = f'ConnectionError'
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))

    def __call__(self):
        try:
            response = self.session.get(self.referer + '/api/v2/torrents/info?filter=all&reverse=false&sort=downloaded')
            if response.status_code == 200:
                torrents = response.json()

                self.reset_settings('border_subtitle')
                self.reset_settings('styles.border_subtitle_color')

                if torrents:
                    return DataFrame.from_dict(torrents)
            elif response.status_code in [401, 403]:
                self.__post_init__()
            else:
                self.border_subtitle = f'{response.status_code} {response.reason}'
                self.styles.border_subtitle_color = 'red'
                self.logger.error('Request returned status code {} - {}', response.status_code, response.reason)

        except ConnectionError as e:
            self.border_subtitle = f'ConnectionError'
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))
        except JSONDecodeError as e:
            self.border_subtitle = f'JSONDecodeError'
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))


widget = BitTorrent

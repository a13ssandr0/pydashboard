from typing import Any

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


class QBitTorrent(TableModule):
    justify = _justify
    colorize = {'state': colorize}

    def __init__(self, *, host: str, username: str, password: str, port: int = 8080, scheme: str = 'http',
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] = ('downloaded', False),
                 columns: list[str] = ('state', 'progress', 'ratio', 'name'), human_readable: bool = True,
                 **kwargs: Any):
        """

        Args:
            host: qBittorrent server IP or FQDN
            username: qBittorrent username
            password: qBittorrent password
            port: qBittorrent server port
            scheme: http or https
            sort: See [Sorting](../containers/tablemodule.md#sorting)
            columns: See [Available columns](qbittorrent.md#qbittorrent.QBitTorrent--available-columns)
            human_readable: Convert numbers to human readable strings
            **kwargs: See [TableModule](../containers/tablemodule.md)

        # Available columns:
        Source: [qBittorrent WebUI API](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-5.0)#get-torrent-list)

        Name                 | Description
        ---------------------|------------
        `added_on`           | Time (Unix Epoch) when the torrent was added to the client
        `amount_left`        | Amount of data left to download (bytes)
        `auto_tmm`           | Whether this torrent is managed by Automatic Torrent Management
        `availability`       | Percentage of file pieces currently available
        `category`           | Category of the torrent
        `completed`          | Amount of transfer data completed (bytes)
        `completion_on`      | Time (Unix Epoch) when the torrent completed
        `content_path`       | Absolute path of torrent content (root path for multifile torrents, absolute file path for singlefile torrents)
        `dl_limit`           | Torrent download speed limit (bytes/s). `-1` if unlimited.
        `dlspeed`            | Torrent download speed (bytes/s)
        `downloaded`         | Amount of data downloaded
        `downloaded_session` | Amount of data downloaded this session
        `eta`                | Torrent ETA (seconds)
        `f_l_piece_prio`     | True if first last piece are prioritized
        `force_start`        | True if force start is enabled for this torrent
        `hash`               | Torrent hash
        `isPrivate`          | True if torrent is from a private tracker (added in 5.0.0)
        `last_activity`      | Last time (Unix Epoch) when a chunk was downloaded/uploaded
        `magnet_uri`         | Magnet URI corresponding to this torrent
        `max_ratio`          | Maximum share ratio until torrent is stopped from seeding/uploading
        `max_seeding_time`   | Maximum seeding time (seconds) until torrent is stopped from seeding
        `name`               | Torrent name
        `num_complete`       | Number of seeds in the swarm
        `num_incomplete`     | Number of leechers in the swarm
        `num_leechs`         | Number of leechers connected to
        `num_seeds`          | Number of seeds connected to
        `priority`           | Torrent priority. Returns -1 if queuing is disabled or torrent is in seed mode
        `progress`           | Torrent progress (percentage/100)
        `ratio`              | Torrent share ratio. Max ratio value: 9999.
        `ratio_limit`        | TODO (what is different from `max_ratio`?)
        `reannounce`         | Time until the next tracker reannounce
        `save_path`          | Path where this torrent's data is stored
        `seeding_time`       | Torrent elapsed time while complete (seconds)
        `seeding_time_limit` | TODO (what is different from `max_seeding_time`?) seeding_time_limit is a per torrent setting, when Automatic Torrent Management is disabled, furthermore then max_seeding_time is set to seeding_time_limit for this torrent. If Automatic Torrent Management is enabled, the value is -2. And if max_seeding_time is unset it have a default value -1.
        `seen_complete`      | Time (Unix Epoch) when this torrent was last seen complete
        `seq_dl`             | True if sequential download is enabled
        `size`               | Total size (bytes) of files selected for download
        `state`              | Torrent state. See table here below for the possible values
        `super_seeding`      | True if super seeding is enabled
        `tags`               | Comma-concatenated tag list of the torrent
        `time_active`        | Total active time (seconds)
        `total_size`         | Total size (bytes) of all file in this torrent (including unselected ones)
        `tracker`            | The first tracker with working status. Returns empty string if no tracker is working.
        `up_limit`           | Torrent upload speed limit (bytes/s). `-1` if unlimited.
        `uploaded`           | Amount of data uploaded
        `uploaded_session`   | Amount of data uploaded this session
        `upspeed`            | Torrent upload speed (bytes/s)
        """
        super().__init__(host=host, username=username, password=password, port=port, scheme=scheme, sort=sort,
                         columns=columns, human_readable=human_readable, **kwargs)
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


widget = QBitTorrent

from pandas import DataFrame
from requests import JSONDecodeError, Session

from basemod import TableModule
from helpers import noneg
from helpers.units import (duration_fmt, perc_fmt, sizeof_fmt, speedof_fmt,
                           time_fmt)

states_map = {
    'allocating':'A',
    'downloading':'D',
    'checkingDL':'CD',
    'forcedDL':'FD',
    'metaDL':'MD',
    'pausedDL':'PD',
    'queuedDL':'QD',
    'stalledDL':'SD',
    'error':'E',
    'missingFiles':'MF',
    'uploading':'U',
    'checkingUP':'CU',
    'forcedUP':'FU',
    'pausedUP':'PU',
    'queuedUP':'QU',
    'stalledUP':'SU',
    'queuedChecking': 'QC',
    'checkingResumeData':'CR',
    'moving':'MV',
    'unknown':'?'
}


colors_map = {
    "allocating": 'green',
    "downloading": 'green',
    "checkingDL": 'yellow',
    "forcedDL": 'cyan',
    "metaDL": 'blue',
    "pausedDL": 'darkgray',
    "queuedDL": 'blue',
    "stalledDL": 'yellow',
    "error": 'red',
    "missingFiles": 'red',
    "uploading": 'green',
    "checkingUP": 'yellow',
    "forcedUP": 'cyan',
    "pausedUP": 'darkgray',
    "queuedUP": 'blue',
    "stalledUP": 'yellow',
    "queuedChecking": 'blue',
    "checkingResumeData": 'yellow',
    "moving": 'green',
    "unknown": 'magenta'
}


_justify = {
    'added_on':           'left',
    'amount_left':        'right',
    'auto_tmm':           'left',
    'availability':       'right',
    'category':           'left',
    'completed':          'right',
    'completion_on':      'left',
    'content_path':       'left',
    'dl_limit':           'right',
    'dlspeed':            'right',
    'downloaded':         'right',
    'downloaded_session': 'right',
    'eta':                'left',
    'f_l_piece_prio':     'left',
    'force_start':        'left',
    'hash':               'left',
    'isPrivate':          'left',
    'last_activity':      'left',
    'magnet_uri':         'left',
    'max_ratio':          'right',
    'max_seeding_time':   'left',
    'name':               'left',
    'num_complete':       'right',
    'num_incomplete':     'right',
    'num_leechs':         'right',
    'num_seeds':          'right',
    'priority':           'right',
    'progress':           'right',
    'ratio':              'right',
    'ratio_limit':        'right',
    'save_path':          'left',
    'seeding_time':       'left',
    'seeding_time_limit': 'left',
    'seen_complete':      'left',
    'seq_dl':             'left',
    'size':               'right',
    'state':              'right',
    'super_seeding':      'left',
    'tags':               'left',
    'time_active':        'left',
    'total_size':         'right',
    'tracker':            'left',
    'up_limit':           'right',
    'uploaded':           'right',
    'uploaded_session':   'right',
    'upspeed':            'right',
}

_human = {
    'added_on':           duration_fmt,
    'amount_left':        sizeof_fmt,
    #'auto_tmm':           noop,
    'availability':       perc_fmt,
    #'category':           noop,
    'completed':          sizeof_fmt,
    'completion_on':      time_fmt,
    #'content_path':       noop,
    'dl_limit':           speedof_fmt,
    'dlspeed':            speedof_fmt,
    'downloaded':         sizeof_fmt,
    'downloaded_session': sizeof_fmt,
    'eta':                duration_fmt,
    #'f_l_piece_prio':     noop,
    #'force_start':        noop,
    #'hash':               noop,
    #'isPrivate':          noop,
    'last_activity':      time_fmt,
    #'magnet_uri':         noop,
    'max_ratio':          perc_fmt,
    'max_seeding_time':   duration_fmt,
    #'name':               noop,
    #'num_complete':       noop,
    #'num_incomplete':     noop,
    #'num_leechs':         noop,
    #'num_seeds':          noop,
    'priority':           noneg,
    'progress':           perc_fmt,
    'ratio':              perc_fmt,
    'ratio_limit':        perc_fmt,
    #'save_path':          noop,
    'seeding_time':       duration_fmt,
    'seeding_time_limit': duration_fmt,
    'seen_complete':      time_fmt,
    #'seq_dl':             noop,
    'size':               sizeof_fmt,
    'state':              lambda s: states_map.get(s, '?'),
    #'super_seeding':      noop,
    #'tags':               noop,
    'time_active':        duration_fmt,
    'total_size':         sizeof_fmt,
    #'tracker':            noop,
    'up_limit':           speedof_fmt,
    'uploaded':           sizeof_fmt,
    'uploaded_session':   sizeof_fmt,
    'upspeed':            speedof_fmt,
}

def colorize(state):
    c=colors_map.get(state, colors_map['unknown'])
    return f'[{c}]{state}[/{c}]'


class BitTorrent(TableModule):
    justify=_justify
    colorize={'state': colorize}
    
    def __init__(self, *, host, username, password, port=8080, scheme='http',
                 columns:list[str]=['state', 'progress', 'ratio', 'name'],
                 sort:str|tuple[str,bool]|list[str|tuple[str,bool]]=('downloaded', False),
                 human_readable=True, show_header=False,
                 **kwargs):
        self.host=host
        self.username=username
        self.password=password
        self.port=port
        self.scheme=scheme
        self.humanize = _human if human_readable else None
            
        super().__init__(columns=columns, show_header=show_header, sort=sort, **kwargs)
        
        self.referer = f'{scheme}://{host}:{port}'
        self.url = f'{scheme}://{host}:{port}/api/v2/auth/login'
        
    def __post_init__(self):
        self.session = Session()
        _ = self.session.post(self.url, 
                              data={"username": self.username, "password": self.password}, 
                              headers={'Referer': self.referer})

    def __call__(self):
        try:
            response = self.session.get(self.referer + '/api/v2/torrents/info?filter=all&reverse=false&sort=downloaded')
            if response.status_code == 200:
                torrents = response.json()
        
                if torrents:
                    return DataFrame.from_dict(torrents)
                
            else:
                self.border_subtitle = f'{response.status_code} {response.reason}'
                self.styles.border_subtitle_color = 'red'

        except JSONDecodeError as e:
            self.border_subtitle = f'JSONDecodeError'
            self.styles.border_subtitle_color = 'red'

            
        
    
widget = BitTorrent
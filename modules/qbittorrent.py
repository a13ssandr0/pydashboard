# from multisort import multisort
from pandas import DataFrame
from requests import JSONDecodeError, Session

from basemod import BaseModule
from helpers import noneg
from helpers.strings import ljust, rjust
from helpers.tables import mktable
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
    'added_on':           ljust,
    'amount_left':        rjust,
    'auto_tmm':           ljust,
    'availability':       rjust,
    'category':           ljust,
    'completed':          rjust,
    'completion_on':      ljust,
    'content_path':       ljust,
    'dl_limit':           rjust,
    'dlspeed':            rjust,
    'downloaded':         rjust,
    'downloaded_session': rjust,
    'eta':                ljust,
    'f_l_piece_prio':     ljust,
    'force_start':        ljust,
    'hash':               ljust,
    'isPrivate':          ljust,
    'last_activity':      ljust,
    'magnet_uri':         ljust,
    'max_ratio':          rjust,
    'max_seeding_time':   ljust,
    'name':               ljust,
    'num_complete':       rjust,
    'num_incomplete':     rjust,
    'num_leechs':         rjust,
    'num_seeds':          rjust,
    'priority':           rjust,
    'progress':           rjust,
    'ratio':              rjust,
    'ratio_limit':        rjust,
    'save_path':          ljust,
    'seeding_time':       ljust,
    'seeding_time_limit': ljust,
    'seen_complete':      ljust,
    'seq_dl':             ljust,
    'size':               rjust,
    'state':              ljust,
    'super_seeding':      ljust,
    'tags':               ljust,
    'time_active':        ljust,
    'total_size':         rjust,
    'tracker':            ljust,
    'up_limit':           rjust,
    'uploaded':           rjust,
    'uploaded_session':   rjust,
    'upspeed':            rjust,
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


class BitTorrent(BaseModule):
    def __init__(self, *, host, username, password, port=8080, scheme='http',
                 columns:list[str]=['state', 'progress', 'ratio', 'name'],
                 sort:str|tuple[str,bool]|list[str|tuple[str,bool]]=None,
                 human_readable=True,
                 **kwargs):
        self.host=host
        self.username=username
        self.password=password
        self.port=port
        self.scheme=scheme
        self.columns=columns
        self.human_readable=human_readable
        if isinstance(sort, str):
            self.sortby = [sort]
            self.reverse = [False]
        elif isinstance(sort, (list,tuple)):
            if len(sort)==2 and isinstance(sort[0], str) and isinstance(sort[1], bool):
                self.sortby = [sort[0]]
                self.reverse = [sort[1]]
            else:
                self.sortby = []
                self.reverse = []
                for e in sort:
                    if isinstance(e, (list,tuple)):
                        self.sortby.append(e[0])
                        self.reverse.append(e[1])
                    else:
                        self.sortby.append(e)
                        self.reverse.append(False)
        else:
            self.sortby = ['downloaded']
            self.reverse = [False]
            
        super().__init__(**kwargs)
        
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
        
                if not torrents:
                    return
                
                return mktable(table=DataFrame.from_dict(torrents), 
                            humanize=_human if self.human_readable else None, 
                            justify=_justify, 
                            colorize={'state': colorize}, 
                            sortby=self.sortby, 
                            reverse=self.reverse, 
                            print_header=False,
                            select_columns=self.columns)
            else:
                self.border_subtitle = f'{response.status_code} {response.reason}'
                self.styles.border_subtitle_color = 'red'
                return 
        except JSONDecodeError as e:
            self.border_subtitle = f'JSONDecodeError'
            self.styles.border_subtitle_color = 'red'
            return e.strerror
            
        
    
widget = BitTorrent
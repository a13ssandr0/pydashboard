import psutil
from pandas import DataFrame

from basemod import BaseModule
from helpers.strings import ljust, rjust
from helpers.tables import mktable
from helpers.units import perc_fmt, sizeof_fmt

_names_map = {
    'device': 'Device',
    'fstype': 'Type',
    'total': 'Size',
    'used': 'Used',
    'free': 'Avail',
    'percent': 'Use%',
    'mountpoint': 'Mounted on',
    'opts': 'Options'
}

_justify = {
    'device':     ljust,
    'fstype':     ljust,
    'total':      rjust,
    'used':       rjust,
    'free':       rjust,
    'percent':    rjust,
    'mountpoint': ljust,
    'opts':       ljust,
}

_human = {
    # 'device':     noop,
    # 'fstype':     noop,
    'total':      sizeof_fmt,
    'used':       sizeof_fmt,
    'free':       sizeof_fmt,
    'percent':    perc_fmt,
    # 'mountpoint': noop,
    # 'opts':       noop,
}


class DiskUsage(BaseModule):
    def __init__(self, *, columns:list[str]=['device', 'fstype', 'total', 'used', 'free', 'percent', 'mountpoint'], 
                 exclude:list[str]=None, human_readable=True, sizes:list[int]=None, **kwargs):
        self.columns=columns
        self.exclude=exclude
        self.human_readable=human_readable
        self.sizes=sizes
        super().__init__(**kwargs)
        
    def __call__(self):
        partitions = [{**part._asdict(), **psutil.disk_usage(part.mountpoint)._asdict()} for part in psutil.disk_partitions() if not self.exclude or part.fstype not in self.exclude]
        
        table = DataFrame.from_dict(partitions)
        table['percent'] /= 100
        
        return mktable(table=table, 
                       humanize=_human if self.human_readable else None, 
                       column_names=_names_map,
                       justify=_justify, 
                       sortby='mountpoint', 
                       print_header=True,
                       select_columns=self.columns,
                       sizes=self.sizes)
    
widget = DiskUsage
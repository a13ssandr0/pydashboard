import psutil
from pandas import DataFrame

from containers import TableModule
from utils.units import perc_fmt, sizeof_fmt

_names_map = {
    'device'    : 'Device',
    'fstype'    : 'Type',
    'total'     : 'Size',
    'used'      : 'Used',
    'free'      : 'Avail',
    'percent'   : 'Use%',
    'mountpoint': 'Mounted on',
    'opts'      : 'Options'
}

_justify = {
    'device'    : 'left',
    'fstype'    : 'left',
    'total'     : 'right',
    'used'      : 'right',
    'free'      : 'right',
    'percent'   : 'right',
    'mountpoint': 'left',
    'opts'      : 'left',
}

_human = {
    # 'device':     noop,
    # 'fstype':     noop,
    'total'  : sizeof_fmt,
    'used'   : sizeof_fmt,
    'free'   : sizeof_fmt,
    'percent': perc_fmt,
    # 'mountpoint': noop,
    # 'opts':       noop,
}


class DiskUsage(TableModule):
    column_names = _names_map
    justify = _justify

    def __init__(self, *, columns=None,
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] | None = 'mountpoint',
                 exclude: list[str] = None, human_readable=True, sizes: list[int] = None, **kwargs):
        if columns is None:
            columns = ['device', 'fstype', 'total', 'used', 'free', 'percent', 'mountpoint']
        self.exclude = exclude
        self.humanize = _human if human_readable else None
        super().__init__(columns=columns, show_header=True, sizes=sizes, sort=sort, **kwargs)

    def __call__(self):
        partitions = [{**part._asdict(), **psutil.disk_usage(part.mountpoint)._asdict()} for part in
                      psutil.disk_partitions() if not self.exclude or part.fstype not in self.exclude]

        table = DataFrame.from_records(partitions)
        table['percent'] /= 100

        return table


widget = DiskUsage

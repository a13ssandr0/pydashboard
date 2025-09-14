from typing import Any

import psutil
from pandas import DataFrame

from pydashboard.containers import TableModule
from pydashboard.utils.units import perc_fmt, sizeof_fmt

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

    def __init__(self, *, columns: list[str] = ('device', 'fstype', 'total', 'used', 'free', 'percent', 'mountpoint'),
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] | None = 'mountpoint',
                 exclude: list[str] = None, human_readable: bool = True, **kwargs: Any):
        """

        Args:
            columns: Available columns: <br>`device`, `mountpoint`, `fstype`, `opts`, `total`, `used`, `free`, `percent`
            sort: See [Sorting](../containers/tablemodule.md#sorting)
            exclude: Filesystem types to exclude
            human_readable: Convert sizes to human readable strings
            **kwargs: See [TableModule](../containers/tablemodule.md)
        """
        self.exclude = exclude
        self.humanize = _human if human_readable else None
        super().__init__(columns=columns, show_header=kwargs.pop('show_header', True), exclude=exclude,
                         human_readable=human_readable, sort=sort, **kwargs)

    def __call__(self):
        partitions = [{**part._asdict(), **psutil.disk_usage(part.mountpoint)._asdict()} for part in
                      psutil.disk_partitions() if not self.exclude or part.fstype not in self.exclude]

        table = DataFrame.from_records(partitions)
        table['percent'] /= 100

        return table


widget = DiskUsage

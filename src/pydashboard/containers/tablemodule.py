from typing import Any, Callable, Literal, Optional, cast

import rpyc.utils.classic
from pandas import DataFrame
from rich.text import Text
from textual.widgets import DataTable

from pydashboard.utils.lists import interleave
from .basemodule import BaseModule


class TableModule(BaseModule):
    # after module initialization the object is automatically initialized, but
    # linter is not able to detect the change from type to object, so we force it
    inner: DataTable = DataTable
    column_names = {}
    humanize = None
    justify: dict[str, Literal["default", "left", "center", "right", "full"] | None] = {}
    colorize = None

    def __init__(self, *, columns: list[str] = None, show_header:bool=False, sizes:list[int]=None,
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] = None, **kwargs: Any):
        """

        Args:
            columns: A list of columns to show. Default shows all columns.
            show_header: Set true to show table header.
            sizes: Width (in characters) of each column, 0 fits content. If list is shorted than number
                    of columns, missing column widths will default to 0.
            sort: See [Sorting](tablemodule.md#sorting)
            **kwargs: See [BaseModule](basemodule.md)


        """
        super().__init__(columns=columns, show_header=show_header, sizes=sizes, sort=sort, **kwargs)
        if not columns and sizes:
            raise ValueError("Parameter 'columns' cannot be empty when 'sizes' is not empty")
        self.columns = list(columns) if columns else []
        if sizes is None:
            sizes = []
        self.sizes = list(sizes) + [0] * (len(self.columns) - len(sizes))
        self.sortby = None
        self.reverse = None

        if isinstance(sort, str):
            self.sortby = [sort]
            self.reverse = [False]
        elif isinstance(sort, (list, tuple)):
            if len(sort) == 2 and isinstance(sort[0], str) and isinstance(sort[1], bool):
                self.sortby = [sort[0]]
                self.reverse = [sort[1]]
            else:
                self.sortby = []
                self.reverse = []
                for e in sort:
                    if isinstance(e, (list, tuple)):
                        self.sortby.append(e[0])
                        self.reverse.append(e[1])
                    else:
                        self.sortby.append(e)
                        self.reverse.append(False)

        self.inner.show_header = show_header
        self.inner.show_cursor = False
        self.inner.cell_padding = 0
        self.inner.zebra_stripes = True

    def __call__(self, *args, **kwargs) -> 'Optional[DataFrame]':
        """Method called each time the module has to be updated"""
        pass

    def update(self, *args, **kwargs):
        result = cast(DataFrame, self.call_target(*args, **kwargs))
        if self.remote_host:
            # if running over a remote connection copy the dataframe locally
            result = rpyc.utils.classic.obtain(result)
        self.inner.clear()
        if result is not None and not result.empty:
            if not self.columns:
                self.columns = result.columns.to_list()
                self.make_header()

            result = _mktable(df=result,
                              humanize=self.humanize,
                              justify=self.justify,
                              colorize=self.colorize,
                              sortby=self.sortby,
                              reverse=self.reverse,
                              select_columns=self.columns)
            self.inner.add_rows([interleave(r, '') for r in result])

    def make_header(self):
        if self.inner.show_header:
            columns = [Text(self.column_names.get(col, col), justify=self.justify.get(col, "left")) for col in
                       self.columns]
        else:
            columns = [''] * len(self.columns)

        columns = interleave(columns, '')

        if self.sizes:
            sizes = [s or None for s in self.sizes]
        else:
            sizes = [None] * len(self.columns)

        sizes = interleave(sizes, 1)

        for col, s in zip(columns, sizes):
            self.inner.add_column(col, width=s)

    def on_ready(self, signal):
        self.make_header()
        return super().on_ready(signal)


def _mktable(df: DataFrame, humanize: dict[str, Callable] = None,
             justify: dict[str, Literal["default", "left", "center", "right", "full"] | None] = None,
             colorize: dict[str, Callable] = None,
             sortby: list[str] = None, reverse: list[bool] = None,
             select_columns: str | list[str] = None):
    if justify is None:
        justify = {}

    if sortby:
        if reverse is None:
            df = df.sort_values(sortby)
        else:
            df = df.sort_values(sortby, ascending=[not r for r in reverse])

    if select_columns:
        # exclude unwanted columns here AFTER sorting
        df = df[select_columns]
        columns = select_columns
    else:
        columns = df.columns.to_list()

    if humanize:
        for col, func in humanize.items():
            try:
                # explicitly casting to str to avoid errors in future versions of pandas
                ### FutureWarning: Setting an item of incompatible dtype is deprecated and will raise in a future error of pandas.
                df.loc[:, col] = df[col].map(func).astype(str)
            except KeyError:
                pass

    df = df.astype(str)

    if colorize:
        for col, func in colorize.items():
            try:
                df.loc[:, col] = df[col].map(func)
            except KeyError:
                pass

    table = [r[1].to_list() for r in df.iterrows()]

    for row in table:
        for i in range(len(columns)):
            row[i] = Text.from_markup(row[i], justify=justify.get(columns[i], 'left'))

    return table

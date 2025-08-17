from typing import Callable, Literal

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

    def __init__(self, *, columns: list[str], show_header=False, sizes=None,
                 sort: str | tuple[str, bool] | list[str | tuple[str, bool]] | None = None, **kwargs):
        """

        Args:
            columns:
            show_header:
            sizes:
            sort:
            **kwargs: See [BaseModule](../containers/basemodule.md)
        """
        super().__init__(columns=columns, show_header=show_header, sizes=sizes, sort=sort, **kwargs)
        self.columns = columns
        if sizes is None:
            sizes = [0]
        self.sizes = sizes + [0] * (len(columns) - len(sizes))
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

    def __call__(self, *args, **kwargs) -> 'DataFrame|None':
        """Method called each time the module has to be updated"""
        pass

    def update(self, *args, **kwargs):
        result = self(*args, **kwargs)
        self.inner.clear()
        if result is not None and not result.empty:
            result = _mktable(df=result,
                              humanize=self.humanize,
                              justify=self.justify,
                              colorize=self.colorize,
                              sortby=self.sortby,
                              reverse=self.reverse,
                              select_columns=self.columns)
            self.inner.add_rows([interleave(r, '') for r in result])

    def on_ready(self, signal):
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

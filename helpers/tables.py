from typing import Callable

from pandas import DataFrame

from helpers.strings import ljust


def mktable(table:DataFrame, humanize:dict[str,Callable]=None,
            column_names:dict[str,str]=None,
            justify=None, colorize:dict[str,Callable]=None,
            sortby:list[str]=None, reverse:list[bool]=None, print_header=True,
            select_columns:str|list[str]=None, sizes:list[int]=None):
    
    if justify is None:
        justify = {}

    if sortby:
        if reverse is None:
            table = table.sort_values(sortby)
        else:
            table = table.sort_values(sortby, ascending=[not r for r in reverse])
    
    if select_columns:
        table = table[select_columns]
        columns = select_columns
    else:
        columns = table.columns.to_list()
    
    if humanize:
        for col, func in humanize.items():
            try:
                table[col] = table[col].map(func)
            except KeyError:
                pass
    
    table = table.astype(str)
    
    if sizes:
        for i, s in enumerate(sizes):
            if s == 0: continue
            try:
                table.iloc[:,i] = table.iloc[:,i].map(lambda x: x[:s])
            except IndexError:
                pass
    
    if print_header:
        if column_names:
            widths = [max(table[col].str.len().max(), len(column_names.get(col, col))) for col in table.columns]
        else:
            widths = [max(table[col].str.len().max(), len(col)) for col in table.columns]
    else:
        widths = [table[col].str.len().max() for col in table.columns]
    
    if colorize:
        for col, func in colorize.items():
            try:
                table[col] = table[col].map(func)
            except KeyError:
                pass
        
    # build a list of lists like
    # Header 1    Header 2    Header 3
    # lorem       ipsum       dolor
    # sit         amet        consectetur
    # adipiscing  elit        Curabitur
    table = [r[1].to_list() for r in table.iterrows()]
    if print_header:
        if column_names:
            table.insert(0, [column_names.get(col, col) for col in columns])
        else:
            table.insert(0, columns)
        
    
    for row in table:
        for i in range(len(columns)):
            row[i] = justify.get(columns[i], ljust)(row[i], widths[i])

    return '\n'.join([' '.join(r) for r in table])
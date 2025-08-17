from math import ceil, floor
from typing import Literal


def calc_bars_sizes(content_width: int, bars: Literal['auto', 0, 1, 2]):
    if bars == 'auto' or bars < 1:
        if content_width < 22:
            bars = 2
        else:
            bars = 1
    elif bars > 2:
        bars = 2

    if bars == 1:
        lbar = ceil(content_width / 2)
        rbar = floor(content_width / 2)
    else:
        lbar = rbar = content_width

    return bars, lbar, rbar


def create_bar(max_w: int, perc: int | float, text: str = '', pre_txt='', color='red'):
    if perc is None:
        # percentage can be None in case of errors and pre_txt will display
        # the associated message
        return f"[{color}]{pre_txt}[/{color}]"

    max_w -= len(pre_txt)

    if max_w <= 0:
        # preceding text takes precedence and can take all the available space
        return pre_txt

    max_w -= 2  # square brackets at both ends
    text = text[:max_w]  # cut text if too long to prevent overflow

    perc = min(max(perc, 0), 100)  # clamp perc between 0 and 100

    color_width = round((perc / 100) * max_w)

    bar = '|' * color_width  # fill the row
    bar = bar[:(max_w - len(text))]  # making room for the text

    bar = f"{bar}{' ' * (max_w - len(bar) - len(text))}{text}"

    bar = f"[{color}]{bar[:color_width]}[/{color}]{bar[color_width:]}"

    return fr'{pre_txt}\[{bar}]'

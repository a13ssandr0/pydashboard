from typing import List, Literal, Optional, Union

import rich.text
from rich.style import Style
from rich.text import Span

from containers import BaseModule


class Text(BaseModule):
    def __init__(
        self,
        *,
        text: str = "",
        style: Union[str, Style] = "",
        align: Optional[Literal["default", "left", "center", "right", "full"]] = None,
        overflow: Optional[Literal["fold", "crop", "ellipsis", "ignore"]] = None,
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: Optional[int] = None,
        spans: Optional[List[Span]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.text = text
        self.style = style
        self.align = align
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        self.tab_size = tab_size
        self.spans = spans
        self.inner.update(
            rich.text.Text(
                text,
                style=style,
                justify=align,
                overflow=overflow,
                no_wrap=no_wrap,
                end=end,
                tab_size=tab_size,
                spans=spans,
            )
        )
    
    def on_ready(self, _):
        pass


widget = Text
